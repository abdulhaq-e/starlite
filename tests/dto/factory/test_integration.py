from __future__ import annotations

from dataclasses import dataclass, field

from typing_extensions import Annotated

from litestar import post
from litestar.datastructures import UploadFile
from litestar.dto.factory import DTOConfig, dto_field
from litestar.dto.factory.stdlib.dataclass import DataclassDTO
from litestar.enums import MediaType, RequestEncodingType
from litestar.params import Body
from litestar.testing import create_test_client


def test_url_encoded_form_data() -> None:
    @dataclass
    class User:
        name: str
        age: int
        read_only: str = field(default="read-only", metadata=dto_field("read-only"))

    @post(dto=DataclassDTO[User], signature_namespace={"User": User})
    def handler(data: User = Body(media_type=RequestEncodingType.URL_ENCODED)) -> User:
        return data

    with create_test_client(route_handlers=[handler], debug=True) as client:
        response = client.post(
            "/",
            content=b"id=1&name=John&age=42&read_only=whoops",
            headers={"Content-Type": "application/x-www-form-urlencoded"},
        )
        assert response.json() == {"name": "John", "age": 42, "read_only": "read-only"}


async def test_multipart_encoded_form_data() -> None:
    @dataclass
    class Payload:
        file: UploadFile
        forbidden: UploadFile = field(
            default=UploadFile(content_type="text/plain", filename="forbidden", file_data=b"forbidden"),
            metadata=dto_field("read-only"),
        )

    @post(
        dto=DataclassDTO[Payload], return_dto=None, signature_namespace={"Payload": Payload}, media_type=MediaType.TEXT
    )
    async def handler(data: Payload = Body(media_type=RequestEncodingType.MULTI_PART)) -> bytes:
        return await data.forbidden.read()

    with create_test_client(route_handlers=[handler], debug=True) as client:
        response = client.post(
            "/",
            files={"file": b"abc123", "forbidden": b"123abc"},
        )
        assert response.content == b"forbidden"


def test_renamed_field() -> None:
    @dataclass
    class Foo:
        bar: str

    config = DTOConfig(rename_fields={"bar": "baz"})
    dto = DataclassDTO[Annotated[Foo, config]]

    @post(dto=dto, signature_namespace={"Foo": Foo})
    def handler(data: Foo) -> Foo:
        assert data.bar == "hello"
        return data

    with create_test_client(route_handlers=[handler], debug=True) as client:
        response = client.post("/", json={"baz": "hello"})
        assert response.json() == {"baz": "hello"}


def test_fields_alias_generator() -> None:
    @dataclass
    class Foo:
        bar: str

    config = DTOConfig(rename_strategy=lambda x: x.upper())
    dto = DataclassDTO[Annotated[Foo, config]]

    @post(dto=dto, signature_namespace={"Foo": Foo})
    def handler(data: Foo) -> Foo:
        assert data.bar == "hello"
        return data

    with create_test_client(route_handlers=[handler], debug=True) as client:
        response = client.post("/", json={"BAR": "hello"})
        assert response.json() == {"BAR": "hello"}
