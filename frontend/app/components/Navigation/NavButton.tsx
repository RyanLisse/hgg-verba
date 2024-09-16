"use client";

import React from "react";
import VerbaButton from "./VerbaButton";
import { PageType } from "@/app/types"; // Update this import

// Remove this line as we're now importing PageType from types.ts
// type PageType = "CHAT" | "DOCUMENTS" | "STATUS" | "IMPORT_DATA" | "SETTINGS" | "RAG" | "ADD";

interface NavbarButtonProps {
  hide: boolean;
  Icon: React.ComponentType;
  title: string;
  currentPage: PageType;
  setCurrentPage: (page: PageType) => void;
  setPage: PageType;
}

const NavbarButton: React.FC<NavbarButtonProps> = ({
  hide,
  Icon,
  title,
  currentPage,
  setCurrentPage,
  setPage,
}) => {
  return (
    <VerbaButton
      title={title}
      Icon={Icon}
      selected_color="bg-primary-verba"
      selected={currentPage === setPage}
      onClick={() => {
        setCurrentPage(setPage);
      }}
      disabled={hide}
    />
  );
};

export default NavbarButton;
