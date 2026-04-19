import styles from "./DashboardCard.module.scss";

export default function DashboardCard({ title, value }) {
  return (
    <div className={styles.card}>
      <p>{title}</p>
      <h2>{value}</h2>
    </div>
  );
}
