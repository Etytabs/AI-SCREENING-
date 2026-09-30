"use client";

import { useState } from "react";

interface Props {
  accept: string;
  multiple?: boolean;
  disabled?: boolean;
  label: string;
  hint: string;
  onFiles: (files: File[]) => void;
  inputLabel?: string;
}

export function FileDrop({ accept, multiple, disabled, label, hint, onFiles, inputLabel }: Props) {
  const [dragging, setDragging] = useState(false);
  return (
    <label
      className={`dropzone ws-dropzone${dragging ? " dragging" : ""}${disabled ? " busy" : ""}`}
      onDragOver={(e) => { e.preventDefault(); if (!disabled) setDragging(true); }}
      onDragLeave={() => setDragging(false)}
      onDrop={(e) => {
        e.preventDefault();
        setDragging(false);
        if (!disabled && e.dataTransfer.files.length) onFiles(Array.from(e.dataTransfer.files));
      }}
    >
      <input
        type="file"
        accept={accept}
        multiple={multiple}
        disabled={disabled}
        aria-label={inputLabel ?? label}
        onChange={(e) => {
          const files = Array.from(e.target.files ?? []);
          if (files.length) onFiles(files);
          e.target.value = "";
        }}
      />
      <div className="dropzone-icon" aria-hidden="true">↑</div>
      <b>{label}</b>
      <span>{hint}</span>
      {!disabled && <em>Choose file{multiple ? "s" : ""}</em>}
    </label>
  );
}
