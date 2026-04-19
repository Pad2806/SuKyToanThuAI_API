import { useState, useEffect } from "react";
import { LOADING_MSGS } from "../data/constants";
import "../styles/LoadingOverlay.css";

export default function LoadingOverlay({ visible }) {
  const [msgIdx, setMsgIdx] = useState(0);

  useEffect(() => {
    if (!visible) return;
    setMsgIdx(0);
    const iv = setInterval(
      () => setMsgIdx((i) => (i + 1) % LOADING_MSGS.length),
      700
    );
    return () => clearInterval(iv);
  }, [visible]);

  if (!visible) return null;

  return (
    <div className="loading-overlay">
      <div className="loading-overlay__spinner" />
      <div className="loading-overlay__msg">{LOADING_MSGS[msgIdx]}</div>
      <div className="loading-overlay__sub">
        AI đang làm việc chăm chỉ, vui lòng chờ một chút
      </div>
      <div className="loading-overlay__bar-wrap">
        <div className="loading-overlay__bar" />
      </div>
    </div>
  );
}
