from fastapi import Body, Depends
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
