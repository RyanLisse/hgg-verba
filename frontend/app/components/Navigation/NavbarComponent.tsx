"use client";

import type { PageType } from "@/app/types";
import { closeOnClick } from "@/app/util";
import Image from "next/image";
import type React from "react";
import {
  IoAddCircle,
  IoChatbubbleSharp,
  IoDocumentSharp,
  IoSettingsSharp,
} from "react-icons/io5";
import { TiThMenu } from "react-icons/ti";
import NavbarButton from "./NavButton";
import VerbaButton from "./VerbaButton";

interface NavbarProps {
  imageSrc: string;
  title: string;
  subtitle: string;
  version: string;
  currentPage: PageType;
  production: "Local" | "Demo" | "Production";
  setCurrentPage: (page: PageType) => void;
}

const Navbar: React.FC<NavbarProps> = ({
  imageSrc,
  title,
  subtitle,
  currentPage,
  setCurrentPage,
  production,
}) => {
  return (
    <div className="flex justify-between items-center mb-10">
      {/* Logo, Title, Subtitle */}
      <div className="flex flex-row items-center gap-5">
        <Image
          src={imageSrc}
          alt="Logo"
          width={50}
          height={50}
          className="flex rounded-lg w-[50px] md:w-[80px] md:h-[80px] object-contain"
        />
        <div className="flex flex-col lg:flex-row lg:items-end justify-center lg:gap-3">
          <p className="text-2xl md:text-3xl text-text-verba">{title}</p>
          <p className="text-sm md:text-base text-text-alt-verba font-light">
            {subtitle}
          </p>
        </div>
        <div className="flex md:hidden flex-col items-center gap-3 justify-between">
          <div className="dropdown dropdown-hover">
            <VerbaButton Icon={TiThMenu} title="Menu" />
            <ul
              tabIndex={0}
              className="dropdown-content dropdown-left z-[1] menu p-2 shadow bg-base-100 rounded-box w-52"
            >
              <li key={"Menu Button1"}>
                <a
                  className={currentPage === "CHAT" ? "font-bold" : ""}
                  onClick={() => {
                    setCurrentPage("CHAT");
                    closeOnClick();
                  }}
                >
                  Chat
                </a>
              </li>
              <li key={"Menu Button2"}>
                <a
                  className={currentPage === "DOCUMENTS" ? "font-bold" : ""}
                  onClick={() => {
                    setCurrentPage("DOCUMENTS");
                    closeOnClick();
                  }}
                >
                  Documents
                </a>
              </li>
              {production !== "Demo" && (
                <li key={"Menu Button4"}>
                  <a
                    className={currentPage === "IMPORT_DATA" ? "font-bold" : ""}
                    onClick={() => {
                      setCurrentPage("IMPORT_DATA");
                      closeOnClick();
                    }}
                  >
                    Import Data
                  </a>
                </li>
              )}
              {production !== "Demo" && (
                <li key={"Menu Button5"}>
                  <a
                    className={currentPage === "SETTINGS" ? "font-bold" : ""}
                    onClick={() => {
                      setCurrentPage("SETTINGS");
                      closeOnClick();
                    }}
                  >
                    Settings
                  </a>
                </li>
              )}
            </ul>
          </div>
        </div>
      </div>

      <div className="flex flex-row justify-center items-center">
        {/* Pages */}
        <div className="hidden md:flex flex-row items-center gap-3 justify-between">
          <NavbarButton
            hide={false}
            Icon={IoChatbubbleSharp}
            title="Chat"
            currentPage={currentPage}
            setCurrentPage={setCurrentPage}
            setPage="CHAT"
          />
          {production !== "Demo" && (
            <NavbarButton
              hide={false}
              Icon={IoAddCircle}
              title="Import Data"
              currentPage={currentPage}
              setCurrentPage={setCurrentPage}
              setPage="IMPORT_DATA"
            />
          )}
          <NavbarButton
            hide={false}
            Icon={IoDocumentSharp}
            title="Documents"
            currentPage={currentPage}
            setCurrentPage={setCurrentPage}
            setPage="DOCUMENTS"
          />
          {production !== "Demo" && (
            <NavbarButton
              hide={false}
              Icon={IoSettingsSharp}
              title="Settings"
              currentPage={currentPage}
              setCurrentPage={setCurrentPage}
              setPage="SETTINGS"
            />
          )}
          <div
            className={`sm:h-[3vh] lg:h-[5vh] mx-1 hidden md:block bg-text-alt-verba w-px`}
          ></div>
        </div>
      </div>
    </div>
  );
};

export default Navbar;
