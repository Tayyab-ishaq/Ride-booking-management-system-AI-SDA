from __future__ import annotations

from uuid import UUID, uuid4

from exception.payment_exceptions import PaymentNotFound, PaymentOwnershipError

from .base import PaymentServiceBase


class PaymentMethodService(PaymentServiceBase):
    async def add_method(
        self,
        user_id: UUID,
        method_type: str,
        token_ref: str,
        is_default: bool = False,
    ):
        return await self.repository.create_payment_method(
            method_id=uuid4(),
            user_id=user_id,
            method_type=method_type,
            token_ref=token_ref,
            is_default=is_default,
        )

    async def list_methods(self, user_id: UUID):
        return await self.repository.get_payment_methods_by_user_id(user_id)

    async def delete_method(self, user_id: UUID, method_id: UUID) -> None:
        method = await self.repository.get_payment_method_by_id(method_id)
        if method.user_id != user_id:
            raise PaymentOwnershipError("You are not allowed to remove this payment method")
        await self.repository.delete_payment_method(method_id, user_id)
