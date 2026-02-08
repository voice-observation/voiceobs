"use client";

import { CircleX } from "lucide-react";
import { Toaster as SonnerToaster } from "sonner";

export function Toaster() {
  return (
    <SonnerToaster
      position="top-center"
      richColors
      icons={{
        error: <CircleX size={20} />,
      }}
    />
  );
}
