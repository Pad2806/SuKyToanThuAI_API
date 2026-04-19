import styles from "./EventItem.module.scss";

export default function EventItem({ title, desc, status, image }) {
  return (
    <div className={styles.cmsCard}>
      <div className={styles.cmsThumb}>
        <img src={image} alt={title} loading="lazy" />
      </div>
      <div className={styles.cmsBody}>
        <div className={styles.titleRow}>
          <h4 className={styles.cmsTitle}>{title}</h4>
          <span
            className={status === "Đã đăng" ? styles.published : styles.draft}
          >
            {status}
          </span>
        </div>
        <p className={styles.cmsDesc}>{desc}</p>
      </div>
    </div>
  );
}
