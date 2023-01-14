from enum import Enum
from typing import Optional, Tuple, Iterator

import aws_cdk.aws_dynamodb as dynamodb
from aws_cdk import Tags
from constructs import Construct
import pynamodb.attributes
import pynamodb.indexes
import pynamodb.models

__all__ = ["PynamoDBAttributeType", "PynamoDBTable"]


class PynamoDBAttributeType(Enum):
    """
    DynamoDB Attribute Types for Key
    """

    S = "STRING"
    N = "NUMBER"
    B = "BINARY"


class PynamoDBTable(dynamodb.Table):
    def __init__(
        self,
        scope: Construct,
        id: str,
        *,
        pynamodb_model: "pynamodb.models.Model",
        auto_add_index: bool = True,
        auto_add_tags: bool = True,
        override_default_tag_priority: Optional[int] = None,
        billing_mode: Optional[dynamodb.BillingMode] = None,
        read_capacity: Optional[int] = None,
        write_capacity: Optional[int] = None,
        **kwargs,
    ):
        """AWS CDK DynamoDB table loaded from a pynamodb model
        :param scope: -
        :param id: -
        :param pynamodb_model: The pynamodb model to be loaded
        :param auto_add_index: If `True`, automatically add all indexes from the pynamodb model to the table.
        Default: `True`
        :param auto_add_tags: If `True`, automatically add all tags from the pynamodb model to the table.
        :param override_default_tag_priority: Override tags priority.
        :param billing_mode: Specify how you are charged for read and write throughput and how you manage capacity.
                            If `None` automatically loaded from pynamodb model if exists.
        :param read_capacity: The read capacity for the table.
                            If `None` automatically loaded from pynamodb model if exists.
        :param write_capacity: The write capacity for the table.
                            If `None` automatically loaded from pynamodb model if exists.
        :param kwargs: Additional keyword arguments to pass to the DynamoDB Table constructor
        """
        self.pynamodb_model = pynamodb_model
        meta = pynamodb_model.Meta

        tags = None

        schema = dict()
        if hasattr(meta, "read_capacity_units"):
            schema["read_capacity"] = meta.read_capacity_units
        if hasattr(meta, "write_capacity_units"):
            schema["write_capacity"] = meta.write_capacity_units
        if hasattr(meta, "billing_mode"):
            schema["billing_mode"] = dynamodb.BillingMode(meta.billing_mode)
        if read_capacity is not None:
            schema["read_capacity"] = read_capacity
        if write_capacity is not None:
            schema["write_capacity"] = write_capacity
        if billing_mode is not None:
            schema["billing_mode"] = billing_mode
        if hasattr(meta, "tags"):
            tags = meta.tags

        schema.update(kwargs)

        super().__init__(
            scope,
            id,
            partition_key=self._to_dynamodb_attr(
                pynamodb_model._hash_key_attribute()  # noqa
            ),
            sort_key=self._to_dynamodb_attr(
                pynamodb_model._range_key_attribute()  # noqa
            ),
            **schema,
        )

        if auto_add_index:
            if indexes := getattr(pynamodb_model, "_indexes"):
                for index_name, index in indexes.items():
                    self.add_pynamodb_index(index=index)

        if tags and auto_add_tags:
            for k, v in tags.items():
                Tags.of(self).add(k, v, priority=override_default_tag_priority)

    def add_pynamodb_index(self, index: pynamodb.indexes.Index, **kwargs) -> None:
        self._add_pynamodb_index_to_table(self, index, **kwargs)

    def get_pynamodb_indexes(self) -> Iterator[Tuple[str, pynamodb.indexes.Index]]:
        if indexes := getattr(self.pynamodb_model, "_indexes"):
            for index_name, index in indexes.items():
                yield index_name, index

    @staticmethod
    def _to_dynamodb_attr(
        attribute: Optional[pynamodb.attributes.Attribute],
    ) -> Optional[dynamodb.Attribute]:
        if isinstance(attribute, pynamodb.attributes.Attribute):
            dynamodb_attr_type = PynamoDBAttributeType[attribute.attr_type].value

            return dynamodb.Attribute(
                name=attribute.attr_name,
                type=dynamodb.AttributeType(dynamodb_attr_type),
            )
        return

    @classmethod
    def from_pynamodb_model(
        cls,
        scope: Construct,
        *,
        pynamodb_model: "pynamodb.models.Model",
        billing_mode: Optional[dynamodb.BillingMode] = None,
        read_capacity: Optional[int] = None,
        write_capacity: Optional[int] = None,
        **kwargs,
    ):
        """
        Load model and it's indexes by default.
        The id is loaded from PynamoDB model's `__name__`
        :param scope: -
        :param pynamodb_model: The PynamoDB model to be loaded
        :param billing_mode: Specify how you are charged for read and write throughput and how you manage capacity.
                            If `None` automatically loaded from pynamodb model if exists.
        :param read_capacity: The read capacity for the table.
                            If `None` automatically loaded from pynamodb model if exists.
        :param write_capacity: The write capacity for the table.
                            If `None` automatically loaded from pynamodb model if exists.
        :param kwargs: Additional keyword arguments to pass to the DynamoDB Table constructor
        """
        return cls(
            scope,
            pynamodb_model.__name__,
            pynamodb_model=pynamodb_model,
            billing_mode=billing_mode,
            read_capacity=read_capacity,
            write_capacity=write_capacity,
            **kwargs,
        )

    @classmethod
    def _add_pynamodb_index_to_table(
        cls,
        table: dynamodb.Table,
        index: pynamodb.indexes.Index,
        index_name: Optional[str] = None,
        read_capacity: Optional[int] = None,
        write_capacity: Optional[int] = None,
        **kwargs,
    ) -> None:
        meta = index.Meta

        projection = meta.projection

        props = dict()
        if hasattr(meta, "index_name"):
            props["index_name"] = meta.index_name
        if hasattr(meta, "read_capacity_units"):
            props["read_capacity"] = meta.read_capacity_units
        if hasattr(meta, "write_capacity_units"):
            props["write_capacity"] = meta.write_capacity_units
        if index_name:
            props["index_name"] = index_name
        if read_capacity:
            props["read_capacity"] = read_capacity
        if write_capacity:
            props["write_capacity"] = write_capacity

        for attr_name, attr in meta.attributes.items():
            if attr.is_hash_key and isinstance(
                index, pynamodb.indexes.GlobalSecondaryIndex
            ):
                props["partition_key"] = cls._to_dynamodb_attr(attr)

            elif attr.is_range_key:
                props["sort_key"] = cls._to_dynamodb_attr(attr)

        props["projection_type"] = dynamodb.ProjectionType(projection.projection_type)

        props["non_key_attributes"] = projection.non_key_attributes

        props.update(kwargs)

        props = {k: v for k, v in props.items() if v is not None}

        if isinstance(index, pynamodb.indexes.GlobalSecondaryIndex):
            table.add_global_secondary_index(**props)

        elif isinstance(index, pynamodb.indexes.LocalSecondaryIndex):
            table.add_local_secondary_index(**props)
