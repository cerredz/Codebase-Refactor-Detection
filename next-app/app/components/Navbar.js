"use client";

import Image from "next/image";
import { useState } from "react";
import { motion, AnimatePresence } from "framer-motion";

export default function Navbar() {
  const [isDropdownOpen, setIsDropdownOpen] = useState(false);

  return (
    <nav className="relative z-10 flex justify-between items-center px-8 py-6">
      <div className="flex items-center space-x-2">
        <div className="w-16 h-16 relative">
          <Image src="/images/logo.png" alt="Refactify Logo" fill className="object-contain" />
        </div>
        <span className="text-xl font-bold">Refactify</span>
      </div>

      <div className="hidden md:flex space-x-8 text-sm tracking-wider">
        {/* Features with Framer Motion Dropdown */}
        <div className="relative" onMouseEnter={() => setIsDropdownOpen(true)} onMouseLeave={() => setIsDropdownOpen(false)}>
          <a href="#features" className="z-50 cursor-pointer hover:text-blue-400 transition-colors cursor-pointer tracking-wider font-bold">
            Features
          </a>

          {/* Animated Dropdown Menu with Framer Motion */}
          <AnimatePresence>
            {isDropdownOpen && (
              <motion.div
                initial={{ opacity: 0, y: -10, scale: 0.95 }}
                animate={{ opacity: 1, y: 0, scale: 1 }}
                exit={{ opacity: 0, y: -10, scale: 0.95 }}
                transition={{
                  duration: 0.2,
                  ease: [0.23, 1, 0.32, 1],
                  type: "spring",
                  stiffness: 300,
                  damping: 30,
                }}
                className="absolute z-50 top-full left-1/2 transform -translate-x-[400px] mt-2 w-80 bg-gray-900/95 backdrop-blur-sm border border-gray-700 rounded-lg shadow-2xl"
              >
                <motion.div className="p-6" initial={{ opacity: 0 }} animate={{ opacity: 1 }} transition={{ delay: 0.1, duration: 0.2 }}>
                  <h3 className="text-lg text-blue-400 font-semibold mb-4 normal-case tracking-normal">Key Features</h3>
                  <motion.ul
                    className="space-y-6 text-gray-300 normal-case tracking-normal text-sm"
                    initial="hidden"
                    animate="visible"
                    variants={{
                      hidden: { opacity: 0 },
                      visible: {
                        opacity: 1,
                        transition: {
                          staggerChildren: 0.05,
                          delayChildren: 0.1,
                        },
                      },
                    }}
                  >
                    {[
                      {
                        title: "Massive Codebase Support:",
                        description: "Upload millions of lines across thousands of files and get blazingly fast similarity analysis in seconds",
                      },
                      {
                        title: "LSH Algorithm:",
                        description: "Advanced Locality Sensitive Hashing for efficient duplicate detection",
                      },
                      {
                        title: "Cross-File Analysis:",
                        description: "Identify similar code patterns across different files and modules",
                      },
                      {
                        title: "Multi-Language:",
                        description: "Support for Python, JavaScript, Java, C++, and more",
                      },
                      {
                        title: "CLI & API:",
                        description: "Command-line interface and REST API for seamless integration",
                      },
                      {
                        title: "Smart Thresholds:",
                        description: "Configurable similarity detection with precise control",
                      },
                    ].map((feature, index) => (
                      <motion.li
                        key={index}
                        className="space-y-1"
                        variants={{
                          hidden: { opacity: 0, x: -10 },
                          visible: { opacity: 1, x: 0 },
                        }}
                        transition={{ duration: 0.3, ease: "easeOut" }}
                      >
                        <div className="flex items-center space-x-2">
                          <motion.div
                            className="w-1.5 h-1.5 bg-blue-400 rounded-full flex-shrink-0"
                            initial={{ scale: 0 }}
                            animate={{ scale: 1 }}
                            transition={{ delay: 0.2 + index * 0.05, duration: 0.2 }}
                          />
                          <strong className="text-blue-300 font-semibold">{feature.title}</strong>
                        </div>
                        <p className="ml-3.5 text-white/40 tracking-wider text-xs leading-relaxed">{feature.description}</p>
                      </motion.li>
                    ))}
                  </motion.ul>
                </motion.div>
              </motion.div>
            )}
          </AnimatePresence>
        </div>

        <a
          href="https://github.com/cerredz/Codebase-Refactor-Detection"
          target="_blank"
          rel="noopener noreferrer"
          className="hover:text-blue-400 transition-colors cursor-pointer tracking-wider font-bold"
        >
          Documentation
        </a>
        <a href="#how-it-works" className="hover:text-blue-400 transition-colors cursor-pointer tracking-wider font-bold">
          How It Works
        </a>
      </div>

      <a
        href="https://github.com/cerredz/Codebase-Refactor-Detection"
        target="_blank"
        rel="noopener noreferrer"
        className="font-bold tracking-wider shadow-[inset_0_0_8px_rgba(255,255,255,.25)] bg-gray-800 hover:bg-gray-700 border border-gray-600 hover:border-gray-500 text-white px-6 py-2 rounded-2xl text-sm tracking-wider transition-all duration-300 flex items-center space-x-2"
      >
        <svg className="w-4 h-4" fill="currentColor" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
          <path d="M12 0c-6.626 0-12 5.373-12 12 0 5.302 3.438 9.8 8.207 11.387.599.111.793-.261.793-.577v-2.234c-3.338.726-4.033-1.416-4.033-1.416-.546-1.387-1.333-1.756-1.333-1.756-1.089-.745.083-.729.083-.729 1.205.084 1.839 1.237 1.839 1.237 1.07 1.834 2.807 1.304 3.492.997.107-.775.418-1.305.762-1.604-2.665-.305-5.467-1.334-5.467-5.931 0-1.311.469-2.381 1.236-3.221-.124-.303-.535-1.524.117-3.176 0 0 1.008-.322 3.301 1.23.957-.266 1.983-.399 3.003-.404 1.02.005 2.047.138 3.006.404 2.291-1.552 3.297-1.23 3.297-1.30.653 1.653.242 2.874.118 3.176.77.84 1.235 1.911 1.235 3.221 0 4.609-2.807 5.624-5.479 5.921.43.372.823 1.102.823 2.222v3.293c0 .319.192.694.801.576 4.765-1.589 8.199-6.086 8.199-11.386 0-6.627-5.373-12-12-12z" />
        </svg>
        <span>GitHub</span>
      </a>
    </nav>
  );
}
