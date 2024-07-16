from fastapi import Body, Depends, Path
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from pydantic import BaseModel

from r2r.base import Token, User, UserCreate

from ...engine import R2REngine
from .base_router import BaseRouter

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")


class UserResponse(BaseModel):
    results: User


class TokenResponse(BaseModel):
    results: dict[str, Token]


class PasswordChangeRequest(BaseModel):
    current_password: str
    new_password: str


class PasswordResetRequest(BaseModel):
    email: str


class PasswordResetConfirmRequest(BaseModel):
    new_password: str


class UserProfileUpdate(BaseModel):
    name: str | None = None
    bio: str | None = None
    profile_picture: str | None = None


class AuthRouter(BaseRouter):
    def __init__(self, engine: R2REngine):
        super().__init__(engine)
        self.setup_routes()

    def setup_routes(self):
        @self.router.post("/register", response_model=UserResponse)
        @self.base_endpoint
        async def register_app(user: UserCreate):
            return await self.engine.aregister(user)

        @self.router.post("/verify_email/{verification_code}")
        @self.base_endpoint
        async def verify_email_app(verification_code: str):
            return await self.engine.averify_email(verification_code)

        @self.router.post("/login", response_model=TokenResponse)
        @self.base_endpoint
        async def login_app(form_data: OAuth2PasswordRequestForm = Depends()):
            login_result = await self.engine.alogin(
                form_data.username, form_data.password
            )
            return login_result

        @self.router.get("/user_info", response_model=UserResponse)
        @self.base_endpoint
        async def user_info_app(
            auth_user=Depends(self.engine.providers.auth.auth_wrapper),
        ):
            return auth_user

        @self.router.post(
            "/refresh_access_token", response_model=TokenResponse
        )
        @self.base_endpoint
        async def refresh_access_token_app(
            refresh_token: str = Body(..., embed=True),
            auth_user=Depends(self.engine.providers.auth.auth_wrapper),
        ):
            refresh_result = await self.engine.arefresh_access_token(
                user_email=auth_user.email,
                refresh_token=refresh_token,
            )
            return refresh_result

        @self.router.post("/change_password")
        @self.base_endpoint
        async def change_password_app(
            password_change: PasswordChangeRequest,
            auth_user=Depends(self.engine.providers.auth.auth_wrapper),
        ):
            return await self.engine.achange_password(
                auth_user,
                password_change.current_password,
                password_change.new_password,
            )

        @self.router.post("/request_password_reset")
        @self.base_endpoint
        async def request_password_reset_app(
            reset_request: PasswordResetRequest,
        ):
            return await self.engine.arequest_password_reset(
                reset_request.email
            )

        @self.router.post("/reset_password/{reset_token}")
        @self.base_endpoint
        async def reset_password_app(
            reset_token: str = Path(...),
            reset_confirm: PasswordResetConfirmRequest = Body(...),
        ):
            return await self.engine.aconfirm_password_reset(
                reset_token, reset_confirm.new_password
            )

        @self.router.post("/logout")
        @self.base_endpoint
        async def logout_app(
            auth_user=Depends(self.engine.providers.auth.auth_wrapper),
            token: str = Depends(oauth2_scheme),
        ):
            return await self.engine.alogout(token)

        @self.router.get("/profile", response_model=UserResponse)
        @self.base_endpoint
        async def get_profile_app(
            auth_user=Depends(self.engine.providers.auth.auth_wrapper),
        ):
            return await self.engine.aget_user_profile(auth_user.id)

        @self.router.put("/profile", response_model=UserResponse)
        @self.base_endpoint
        async def update_profile_app(
            profile_update: UserProfileUpdate,
            auth_user=Depends(self.engine.providers.auth.auth_wrapper),
        ):
            return await self.engine.aupdate_user_profile(
                auth_user.id, profile_update.dict(exclude_unset=True)
            )

        @self.router.delete("/account")
        @self.base_endpoint
        async def delete_account_app(
            password: str = Body(..., embed=True),
            auth_user=Depends(self.engine.providers.auth.auth_wrapper),
        ):
            return await self.engine.adelete_user_account(
                auth_user.id, password
            )
