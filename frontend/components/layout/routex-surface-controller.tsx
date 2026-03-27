"use client";

import { usePathname } from "next/navigation";
import { useEffect } from "react";

function getSurfaceFromPathname(pathname: string) {
  if (pathname.startsWith("/dashboard") || pathname.startsWith("/admin")) {
    return "ops";
  }

  return "public";
}

export function RoutexSurfaceController() {
  const pathname = usePathname();

  useEffect(() => {
    const surface = getSurfaceFromPathname(pathname);
    document.body.dataset.rxSurface = surface;
    document.documentElement.dataset.rxSurface = surface;
  }, [pathname]);

  return null;
}
