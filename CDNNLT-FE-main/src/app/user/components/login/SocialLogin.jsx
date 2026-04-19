import { FcGoogle } from "react-icons/fc";
import styles from "./SocialLogin.module.scss";

export default function SocialLogin() {
  return (
    <button className={styles.socialBtn} onClick={() => alert("Google Login")}>
      <FcGoogle className={styles.socialIcon} />
      Tiếp tục với Google
    </button>
  );
}