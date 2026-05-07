from fastapi import APIRouter, Depends, HTTPException, Body
from supabase import Client
from typing import Optional
from pydantic import BaseModel

from core.security import (
    get_supabase_client,
    get_supabase_admin,
    get_current_user_profile,
    get_current_admin,
)

from schemas.auth import RegisterRequest, LoginRequest
from schemas.user import UserResponse

router = APIRouter(tags=["Auth"])

# =========================
# AUTH
# =========================


@router.post("/auth/register")
async def register(
    request: RegisterRequest, supabase_admin: Client = Depends(get_supabase_admin)
):
    auth_user = None

    try:
        # tạo auth user
        auth_response = supabase_admin.auth.admin.create_user(
            {
                "email": request.email,
                "password": request.password,
                "email_confirm": True,
                "user_metadata": {"fullname": request.fullname},
            }
        )

        if not auth_response.user:
            raise Exception("Không tạo được user")

        auth_user = auth_response.user
        user_id = auth_user.id

        # tạo profile
        profile = (
            supabase_admin.table("users")
            .insert(
                {
                    "id": user_id,
                    "email": request.email,
                    "fullname": request.fullname,
                    "role": request.role,
                    "language_preference": "vi",
                    "is_active": True,
                }
            )
            .execute()
        )

        return {"message": "Đăng ký thành công", "user": profile.data}

    except Exception as e:
        if auth_user:
            try:
                supabase_admin.auth.admin.delete_user(auth_user.id)
            except:
                pass

        raise HTTPException(status_code=400, detail=str(e))


@router.post("/auth/login")
async def login(request: LoginRequest, supabase: Client = Depends(get_supabase_client)):
    try:
        response = supabase.auth.sign_in_with_password(
            {"email": request.email, "password": request.password}
        )

        if not response.user or not response.session:
            raise HTTPException(status_code=401, detail="Sai thông tin")

        user_id = response.user.id

        profile_res = (
            supabase.table("users").select("*").eq("id", user_id).single().execute()
        )

        profile = profile_res.data

        if not profile:
            raise HTTPException(status_code=404, detail="Không có profile")

        return {
            "access_token": response.session.access_token,
            "refresh_token": response.session.refresh_token,
            "user": profile,
        }

    except Exception as e:
        raise HTTPException(status_code=401, detail=str(e))


@router.get("/auth/me")
async def get_me(current_user=Depends(get_current_user_profile)):
    return UserResponse(**current_user)


@router.post("/auth/refresh")
async def refresh_token(
    refresh_token: str = Body(...), supabase: Client = Depends(get_supabase_client)
):
    try:
        response = supabase.auth.refresh_session({"refresh_token": refresh_token})

        session = response.session

        if not session:
            raise HTTPException(status_code=401)

        return {
            "access_token": session.access_token,
            "refresh_token": session.refresh_token,
        }

    except Exception as e:
        raise HTTPException(status_code=401, detail=str(e))


# =========================
# USER PROFILE
# =========================


class UpdateProfileRequest(BaseModel):
    fullname: Optional[str] = None
    phone: Optional[str] = None
    birthYear: Optional[int] = None
    gender: Optional[str] = None
    school: Optional[str] = None
    grade: Optional[str] = None
    bio: Optional[str] = None
    language_preference: Optional[str] = None


@router.put("/users/me")
async def update_profile(
    request: UpdateProfileRequest,
    current_user=Depends(get_current_user_profile),
    supabase: Client = Depends(get_supabase_client),
):
    user_id = current_user["id"]

    update_data = request.dict(exclude_unset=True)

    if not update_data:
        raise HTTPException(status_code=400, detail="Không có dữ liệu")

    res = supabase.table("users").update(update_data).eq("id", user_id).execute()

    return {"message": "Cập nhật thành công", "data": res.data}


# =========================
# ADMIN - USER MANAGEMENT
# =========================


class CreateUserRequest(BaseModel):
    email: str
    password: str
    fullname: str
    role: str = "student"  # student | teacher | admin


class UpdateUserRequest(BaseModel):
    fullname: Optional[str] = None
    role: Optional[str] = None
    is_active: Optional[bool] = None
    password: Optional[str] = None

@router.get("/admin/users")
async def get_all_users(
    admin = Depends(get_current_admin),
    supabase_admin: Client = Depends(get_supabase_admin)
):
    """Lấy danh sách tất cả users - Dùng cho Admin Dashboard"""
    response = supabase_admin.table("users").select("*").neq("role", "admin").order("created_at", desc=True).execute()
    return response.data


@router.post("/admin/users")
async def admin_create_user(
    request: CreateUserRequest,
    admin = Depends(get_current_admin),
    supabase_admin: Client = Depends(get_supabase_admin)
):
    """Admin tạo user mới"""
    auth_user = None
    try:
        # Tạo user trong Auth
        auth_response = supabase_admin.auth.admin.create_user({
            "email": request.email,
            "password": request.password,
            "email_confirm": True,
            "user_metadata": {"fullname": request.fullname}
        })

        auth_user = auth_response.user
        user_id = auth_user.id

        # Tạo profile
        profile = supabase_admin.table("users").insert({
            "id": user_id,
            "email": request.email,
            "fullname": request.fullname,
            "role": request.role,
            "language_preference": "vi",
            "is_active": True
        }).execute()

        return {"message": "Tạo người dùng thành công", "data": profile.data[0]}

    except Exception as e:
        if auth_user:
            try:
                supabase_admin.auth.admin.delete_user(auth_user.id)
            except:
                pass
        raise HTTPException(status_code=400, detail=str(e))

@router.put("/admin/users/{user_id}")
async def admin_update_user(
    user_id: str,
    request: UpdateUserRequest,
    admin = Depends(get_current_admin),
    supabase_admin: Client = Depends(get_supabase_admin)
):
    update_data = request.dict(exclude_unset=True)
    password = update_data.pop("password", None)

    try:
        # 1. Cập nhật thông tin profile
        if update_data:
            supabase_admin.table("users").update(update_data).eq("id", user_id).execute()

        # 2. Cập nhật mật khẩu (nếu có)
        if password:
            supabase_admin.auth.admin.update_user_by_id(
                user_id,
                {"password": password}
            )

        return {"message": "Cập nhật người dùng thành công"}

    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.delete("/admin/users/{user_id}")
async def admin_delete_user(
    user_id: str,
    admin = Depends(get_current_admin),
    supabase_admin: Client = Depends(get_supabase_admin)
):
    try:
        # Xóa Auth user
        supabase_admin.auth.admin.delete_user(user_id)
        # Xóa profile
        supabase_admin.table("users").delete().eq("id", user_id).execute()
        
        return {"message": "Đã xóa người dùng thành công"}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.put("/auth/change-password")
async def change_password(
    current_password: str = Body(...),
    new_password: str = Body(...),
    supabase: Client = Depends(get_supabase_client),
    current_user=Depends(get_current_user_profile),
):
    try:
        email = current_user["email"]

        # 👉 1. verify mật khẩu cũ
        login_res = supabase.auth.sign_in_with_password(
            {"email": email, "password": current_password}
        )

        if not login_res.user:
            raise HTTPException(status_code=400, detail="Mật khẩu hiện tại không đúng")

        # 👉 2. update password
        update_res = supabase.auth.update_user({"password": new_password})

        if not update_res.user:
            raise HTTPException(status_code=400, detail="Không thể cập nhật mật khẩu")

        return {"message": "Đổi mật khẩu thành công"}

    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Lỗi đổi mật khẩu: {str(e)}")
