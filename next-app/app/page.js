"use client";
import Image from "next/image";
import Navbar from "./components/Navbar";
import { useState, useRef } from "react";
import { motion, AnimatePresence } from "framer-motion";

// SimilarRegions Component
const SimilarRegions = ({ result, onClose }) => {
  const [currentSlide, setCurrentSlide] = useState(0);
  const similarRegions = result?.similar_regions || [];
  const totalSlides = similarRegions.length;

  // Helper function to extract filename after "codebase"
  const getCleanFileName = (filePath) => {
    const parts = filePath.split("codebase");
    if (parts.length > 1) {
      return parts[1].replace(/^[\\\/]/, ""); // Remove leading slash/backslash
    }
    return filePath;
  };

  const nextSlide = () => {
    setCurrentSlide((prev) => (prev + 1) % totalSlides);
  };

  const prevSlide = () => {
    setCurrentSlide((prev) => (prev - 1 + totalSlides) % totalSlides);
  };

  if (!result || !similarRegions.length) {
    return (
      <motion.div
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        exit={{ opacity: 0 }}
        className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/60 backdrop-blur-sm"
        onClick={onClose}
      >
        <div className="bg-blue-950/30 backdrop-blur-xl border border-blue-400/30 rounded-2xl p-8 text-center">
          <p className="text-white">No similar regions found in your codebase.</p>
        </div>
      </motion.div>
    );
  }

  const currentRegion = similarRegions[currentSlide];

  return (
    <motion.div
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      exit={{ opacity: 0 }}
      className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/60 backdrop-blur-sm"
      onClick={onClose}
    >
      <motion.div
        initial={{ scale: 0.8, opacity: 0, y: 20 }}
        animate={{ scale: 1, opacity: 1, y: 0 }}
        exit={{ scale: 0.8, opacity: 0, y: 20 }}
        transition={{ type: "spring", damping: 25, stiffness: 500 }}
        className="relative w-full max-w-7xl mx-auto max-h-[90vh] overflow-hidden"
        onClick={(e) => e.stopPropagation()}
      >
        {/* Glassmorphism Container */}
        <div className="relative bg-blue-950/30 backdrop-blur-xl border border-blue-400/30 rounded-2xl shadow-2xl overflow-hidden">
          {/* Blue liquid glass gradient overlay */}
          <div className="absolute inset-0 bg-gradient-to-br from-blue-500/30 via-blue-600/20 to-blue-800/25 pointer-events-none"></div>

          {/* Action buttons */}
          <div className="absolute top-6 right-4 z-50 flex gap-2">
            {/* Download button */}
            <button
              onClick={() => {
                const dataStr = JSON.stringify(result, null, 2);
                const dataBlob = new Blob([dataStr], { type: "application/json" });
                const url = URL.createObjectURL(dataBlob);
                const link = document.createElement("a");
                link.href = url;
                link.download = `refactor-analysis-${new Date().toISOString().split("T")[0]}.json`;
                document.body.appendChild(link);
                link.click();
                document.body.removeChild(link);
                URL.revokeObjectURL(url);
              }}
              className="cursor-pointer w-10 h-10 rounded-full bg-blue-500/20 backdrop-blur-sm border border-blue-400/40 flex items-center justify-center hover:bg-blue-500/30 transition-all duration-200 shadow-inner"
              style={{
                boxShadow: "inset 0 1px 2px rgba(59, 130, 246, 0.3), inset 0 -1px 2px rgba(30, 58, 138, 0.2)",
              }}
            >
              <svg className="w-5 h-5 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M12 10v6m0 0l-3-3m3 3l3-3m2 8H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"
                />
              </svg>
            </button>

            {/* Close button */}
            <button
              onClick={onClose}
              className="cursor-pointer w-10 h-10 rounded-full bg-blue-500/20 backdrop-blur-sm border border-blue-400/40 flex items-center justify-center hover:bg-blue-500/30 transition-all duration-200 shadow-inner"
              style={{
                boxShadow: "inset 0 1px 2px rgba(59, 130, 246, 0.3), inset 0 -1px 2px rgba(30, 58, 138, 0.2)",
              }}
            >
              <svg className="w-5 h-5 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
              </svg>
            </button>
          </div>

          {/* Content */}
          <div className="relative z-10 p-6">
            {/* Header */}
            <div className="flex items-center justify-between mb-6 pr-24">
              <div className="flex items-center gap-3">
                <div
                  className="w-8 h-8 rounded-lg bg-blue-500/30 backdrop-blur-sm border border-blue-400/50 flex items-center justify-center shadow-inner"
                  style={{
                    boxShadow: "inset 0 2px 4px rgba(59, 130, 246, 0.4), inset 0 -2px 4px rgba(30, 58, 138, 0.3)",
                  }}
                >
                  <svg className="w-4 h-4 text-blue-200" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path
                      strokeLinecap="round"
                      strokeLinejoin="round"
                      strokeWidth={2}
                      d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z"
                    />
                  </svg>
                </div>
                <h2 className="text-xl font-semibold text-white">Similar Code Regions</h2>
              </div>

              {/* Slide counter */}
              <div className="flex items-center gap-4">
                <span className="text-sm text-blue-200/80 whitespace-nowrap">
                  {currentSlide + 1} of {totalSlides}
                </span>
                <div className="flex gap-2">
                  <button
                    onClick={prevSlide}
                    disabled={totalSlides <= 1}
                    className="cursor-pointer w-10 h-10 rounded-full bg-blue-500/20 backdrop-blur-sm border border-blue-400/40 flex items-center justify-center hover:bg-blue-500/30 transition-all duration-200 shadow-inner disabled:opacity-50 disabled:cursor-not-allowed"
                    style={{
                      boxShadow: "inset 0 1px 2px rgba(59, 130, 246, 0.3), inset 0 -1px 2px rgba(30, 58, 138, 0.2)",
                    }}
                  >
                    <svg className="w-5 h-5 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 19l-7-7 7-7" />
                    </svg>
                  </button>
                  <button
                    onClick={nextSlide}
                    disabled={totalSlides <= 1}
                    className="cursor-pointer w-10 h-10 rounded-full bg-blue-500/20 backdrop-blur-sm border border-blue-400/40 flex items-center justify-center hover:bg-blue-500/30 transition-all duration-200 shadow-inner disabled:opacity-50 disabled:cursor-not-allowed"
                    style={{
                      boxShadow: "inset 0 1px 2px rgba(59, 130, 246, 0.3), inset 0 -1px 2px rgba(30, 58, 138, 0.2)",
                    }}
                  >
                    <svg className="w-5 h-5 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
                    </svg>
                  </button>
                </div>
              </div>
            </div>

            {/* Code Comparison Container */}
            <div className="grid grid-cols-2 gap-4 h-[70vh]">
              {/* File 1 */}
              <div className="bg-blue-500/10 backdrop-blur-sm border border-blue-400/20 rounded-lg overflow-hidden">
                <div className="bg-blue-500/20 backdrop-blur-sm border-b border-blue-400/20 px-4 py-3">
                  <div className="flex items-center gap-2">
                    <svg className="w-4 h-4 text-blue-300" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path
                        strokeLinecap="round"
                        strokeLinejoin="round"
                        strokeWidth={2}
                        d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"
                      />
                    </svg>
                    <h3 className="text-sm font-medium text-blue-200">{getCleanFileName(currentRegion.file1)}</h3>
                    <span className="text-xs text-blue-300/60">
                      Lines {currentRegion.file1_start}-{currentRegion.file1_end}
                    </span>
                  </div>
                </div>
                <div className="p-4 pb-16 overflow-y-auto h-full scrollbar-thin scrollbar-track-blue-500/5 scrollbar-thumb-blue-500/20 hover:scrollbar-thumb-blue-500/30">
                  <pre className="text-xs text-blue-100/90 whitespace-pre-wrap font-mono leading-relaxed mb-8">{currentRegion.regions.file1}</pre>
                </div>
              </div>

              {/* File 2 */}
              <div className="bg-blue-500/10 backdrop-blur-sm border border-blue-400/20 rounded-lg overflow-hidden">
                <div className="bg-blue-500/20 backdrop-blur-sm border-b border-blue-400/20 px-4 py-3">
                  <div className="flex items-center gap-2">
                    <svg className="w-4 h-4 text-blue-300" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path
                        strokeLinecap="round"
                        strokeLinejoin="round"
                        strokeWidth={2}
                        d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"
                      />
                    </svg>
                    <h3 className="text-sm font-medium text-blue-200">{getCleanFileName(currentRegion.file2)}</h3>
                    <span className="text-xs text-blue-300/60">
                      Lines {currentRegion.file2_start}-{currentRegion.file2_end}
                    </span>
                  </div>
                </div>
                <div className="p-4 pb-16 overflow-y-auto h-full scrollbar-thin scrollbar-track-blue-500/5 scrollbar-thumb-blue-500/20 hover:scrollbar-thumb-blue-500/30">
                  <pre className="text-xs text-blue-100/90 whitespace-pre-wrap font-mono leading-relaxed mb-8">{currentRegion.regions.file2}</pre>
                </div>
              </div>
            </div>

            {/* Analysis Summary */}
            <div className="mt-4 p-3 bg-blue-500/10 backdrop-blur-sm border border-blue-400/20 rounded-lg">
              <div className="flex items-center justify-between text-xs text-blue-200/80">
                <span>Analysis completed in {result.analysis_time?.toFixed(2)}s</span>
                <span>{result.total_regions_found} similar regions found</span>
                <span>Threshold: {result.region_threshold} lines</span>
              </div>
            </div>
          </div>
        </div>
      </motion.div>
    </motion.div>
  );
};

export default function Home() {
  const [showUploader, setShowUploader] = useState(false);
  const [dragActive, setDragActive] = useState(false);
  const [uploading, setUploading] = useState(false);
  const [uploadedFiles, setUploadedFiles] = useState([]);
  const [showSimilarRegions, setShowSimilarRegions] = useState(false);
  const [analysisResult, setAnalysisResult] = useState(null);
  const fileInputRef = useRef(null);

  // Upload files to server
  const uploadFiles = async (files) => {
    setUploading(true);
    const formData = new FormData();

    Array.from(files).forEach((file) => {
      formData.append("files", file);
    });

    try {
      const response = await fetch("/api/refactor", {
        method: "POST",
        body: formData,
      });

      if (response.ok) {
        const result = await response.json();
        setUploadedFiles(result.saved_files);
        setAnalysisResult(result);
        console.log("Files uploaded successfully:", result.saved_files);

        // Close the uploader and show similar regions
        setTimeout(() => {
          setShowUploader(false);
          setShowSimilarRegions(true);
        }, 1000); // Show success for 1 second before closing
      } else {
        console.error("Upload failed");
      }
    } catch (error) {
      console.error("Upload error:", error);
    } finally {
      setUploading(false);
    }
  };

  // Handle drag events
  const handleDrag = (e) => {
    e.preventDefault();
    e.stopPropagation();
    if (e.type === "dragenter" || e.type === "dragover") {
      setDragActive(true);
    } else if (e.type === "dragleave") {
      setDragActive(false);
    }
  };

  // Handle drop event
  const handleDrop = (e) => {
    e.preventDefault();
    e.stopPropagation();
    setDragActive(false);

    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      uploadFiles(e.dataTransfer.files);
    }
  };

  // Handle file input change
  const handleFileInput = (e) => {
    if (e.target.files && e.target.files[0]) {
      uploadFiles(e.target.files);
    }
  };

  // Handle browse button click
  const handleBrowseClick = () => {
    fileInputRef.current?.click();
  };
  return (
    <div className="min-h-screen bg-black text-white relative overflow-hidden">
      {/* Background Image */}
      <div className="absolute inset-0 opacity-30">
        <Image src="/images/vert-glow-blue.png" alt="Background glow" fill className="object-cover" priority />
      </div>

      {/* Additional Blue Glowing Background Elements */}

      {/* Navbar */}
      <Navbar />

      {/* Main Content */}
      <div className="relative z-10 flex flex-col items-center justify-center min-h-[80vh] px-8">
        {/* Central Glow Effect */}
        <div className="absolute inset-0 flex items-center justify-center">
          <div className="w-[32rem] h-[32rem] bg-blue-500 rounded-full opacity-20 blur-3xl animate-pulse"></div>
        </div>

        {/* Central Upload Button with Expanding Circles */}
        <div className="relative z-10 mb-16">
          {/* Expanding Circular Lines */}
          <div className="absolute inset-0 flex items-center justify-center">
            {/* Circle 1 - Innermost */}
            <div className="absolute w-72 h-72 rounded-full border border-blue-400/20 animate-ping" style={{ animationDuration: "3s" }}></div>
            {/* Circle 2 */}
            <div
              className="absolute w-80 h-80 rounded-full border border-blue-400/15 animate-ping"
              style={{ animationDuration: "4s", animationDelay: "0.5s" }}
            ></div>
            {/* Circle 3 */}
            <div
              className="absolute w-96 h-96 rounded-full border border-blue-400/10 animate-ping"
              style={{ animationDuration: "5s", animationDelay: "1s" }}
            ></div>
            {/* Circle 4 - Outermost */}
            <div
              className="absolute w-[28rem] h-[28rem] rounded-full border border-blue-400/5 animate-ping"
              style={{ animationDuration: "6s", animationDelay: "1.5s" }}
            ></div>
          </div>

          <button
            className="cursor-pointer group relative animate-pulse"
            style={{ animation: "buttonPulse 3s ease-in-out infinite" }}
            onClick={() => {
              setShowUploader(true);
              setShowSimilarRegions(false);
              setUploadedFiles([]);
              setAnalysisResult(null);
            }}
          >
            <div className="absolute inset-0 bg-blue-500 rounded-full opacity-30 blur-xl group-hover:opacity-50 transition-opacity duration-300"></div>
            <div className="cursor-pointer relative bg-gray-800/50 backdrop-blur-sm rounded-full w-52 h-52 border border-gray-600 hover:border-blue-400 transition-all duration-300 group-hover:bg-gray-700/50 flex items-center justify-center">
              <span className="text-xs tracking-wider font-bold text-center">
                Upload Your
                <br />
                Codebase
              </span>
            </div>
          </button>
        </div>
      </div>

      {/* Hero Text - Moved to Bottom Left */}
      <div className="absolute bottom-20 left-8 z-10 max-w-2xl">
        <h1 className=" max-w-lg tracking-wider font-semibold leading-wider text-left">
          Transforming codebases through intelligent analysis, precise refactoring, and automated similarity detection.
        </h1>
      </div>

      {/* Footer Info */}
      <footer className="absolute bottom-0 left-0 right-0 z-10 flex justify-between items-center px-8 py-6 text-xs text-white/20  tracking-wider">
        <div className="flex flex-row items-center justify-center gap-3">
          <span>Code Analysis</span>
          <span>•</span>
          <span>Refactoring</span>
          <span>•</span>
          <span>Optimization</span>
        </div>
        <div className="flex space-x-8">
          <span>CLI Available</span>
          <span>•</span>
          <span>API Integration</span>
        </div>
      </footer>

      {/* File Uploader Modal */}
      <AnimatePresence>
        {showUploader && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/60 backdrop-blur-sm"
            onClick={() => setShowUploader(false)}
          >
            <motion.div
              initial={{ scale: 0.8, opacity: 0, y: 20 }}
              animate={{ scale: 1, opacity: 1, y: 0 }}
              exit={{ scale: 0.8, opacity: 0, y: 20 }}
              transition={{ type: "spring", damping: 25, stiffness: 500 }}
              className="relative w-full max-w-md mx-auto"
              onClick={(e) => e.stopPropagation()}
            >
              {/* Glassmorphism Container */}
              <div className="relative bg-blue-950/30 backdrop-blur-xl border border-blue-400/30 rounded-2xl shadow-2xl overflow-hidden">
                {/* Blue liquid glass gradient overlay */}
                <div className="absolute inset-0 bg-gradient-to-br from-blue-500/30 via-blue-600/20 to-blue-800/25 pointer-events-none"></div>

                {/* Close button */}
                <button
                  onClick={(e) => {
                    e.stopPropagation();
                    setShowUploader(false);
                  }}
                  className="cursor-pointer absolute top-4 right-4 z-50 w-8 h-8 rounded-full bg-blue-500/20 backdrop-blur-sm border border-blue-400/40 flex items-center justify-center hover:bg-blue-500/30 transition-all duration-200 shadow-inner"
                  style={{
                    boxShadow: "inset 0 1px 2px rgba(59, 130, 246, 0.3), inset 0 -1px 2px rgba(30, 58, 138, 0.2)",
                  }}
                >
                  <svg className="w-4 h-4 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                  </svg>
                </button>

                {/* Content */}
                <div className="relative z-10 p-8">
                  {/* Header */}
                  <div className="flex items-center gap-3 mb-2">
                    <div
                      className="cursor-pointer w-8 h-8 rounded-lg bg-blue-500/30 backdrop-blur-sm border border-blue-400/50 flex items-center justify-center shadow-inner z-50"
                      onClick={(e) => {
                        e.stopPropagation();
                        setShowUploader(false);
                      }}
                      style={{
                        boxShadow: "inset 0 2px 4px rgba(59, 130, 246, 0.4), inset 0 -2px 4px rgba(30, 58, 138, 0.3)",
                      }}
                    >
                      <svg className="w-4 h-4 text-blue-200" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path
                          strokeLinecap="round"
                          strokeLinejoin="round"
                          strokeWidth={2}
                          d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M15 13l-3-3m0 0l-3 3m3-3v12"
                        />
                      </svg>
                    </div>
                    <h2 className="text-xl font-semibold text-white">{uploading ? "Loading..." : "Upload files"}</h2>
                  </div>

                  <p className="text-sm text-blue-100/80 mb-6">Select and upload the files of your choice</p>

                  {/* Upload Area */}
                  <div className="mb-6">
                    <div
                      className={`border-2 border-dashed rounded-xl p-8 text-center transition-all duration-300 bg-blue-500/10 backdrop-blur-sm shadow-inner ${
                        dragActive ? "border-blue-300/80 bg-blue-500/20" : "border-blue-400/40 hover:border-blue-300/60"
                      }`}
                      style={{
                        boxShadow: "inset 0 2px 8px rgba(30, 58, 138, 0.2), inset 0 -2px 8px rgba(59, 130, 246, 0.1)",
                      }}
                      onDragEnter={handleDrag}
                      onDragLeave={handleDrag}
                      onDragOver={handleDrag}
                      onDrop={handleDrop}
                    >
                      <div className="flex flex-col items-center gap-4">
                        <div
                          className="w-12 h-12 rounded-full bg-blue-500/20 backdrop-blur-sm border border-blue-400/30 flex items-center justify-center shadow-inner"
                          style={{
                            boxShadow: "inset 0 2px 4px rgba(59, 130, 246, 0.3), inset 0 -2px 4px rgba(30, 58, 138, 0.2)",
                          }}
                        >
                          {uploading ? (
                            <svg className="w-6 h-6 text-blue-200 animate-spin" fill="none" viewBox="0 0 24 24">
                              <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                              <path
                                className="opacity-75"
                                fill="currentColor"
                                d="m4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"
                              ></path>
                            </svg>
                          ) : (
                            <svg className="w-6 h-6 text-blue-200" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                              <path
                                strokeLinecap="round"
                                strokeLinejoin="round"
                                strokeWidth={2}
                                d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M15 13l-3-3m0 0l-3 3m3-3v12"
                              />
                            </svg>
                          )}
                        </div>
                        <div>
                          <p className="text-white font-medium mb-1">{uploading ? "Uploading..." : "Choose a file or drag & drop it here"}</p>
                          <p className="text-xs text-blue-200/70">
                            {uploadedFiles.length > 0
                              ? `${uploadedFiles.length} file(s) uploaded successfully`
                              : "All file formats supported, up to 50MB per file"}
                          </p>
                        </div>
                        <button
                          onClick={handleBrowseClick}
                          disabled={uploading}
                          className="cursor-pointer px-6 py-2 bg-blue-500/25 backdrop-blur-sm border border-blue-400/40 rounded-lg text-white text-sm font-medium hover:bg-blue-500/35 transition-all duration-200 shadow-inner disabled:opacity-50 disabled:cursor-not-allowed"
                          style={{
                            boxShadow:
                              "inset 0 2px 4px rgba(59, 130, 246, 0.4), inset 0 -2px 4px rgba(30, 58, 138, 0.3), 0 4px 8px rgba(30, 58, 138, 0.2)",
                          }}
                        >
                          {uploading ? "Uploading..." : "Browse File"}
                        </button>
                      </div>
                    </div>

                    {/* Hidden file input */}
                    <input ref={fileInputRef} type="file" multiple onChange={handleFileInput} className="hidden" accept="*/*" />

                    {/* Uploaded files list */}
                    {uploadedFiles.length > 0 && (
                      <div className="mt-4 p-4 bg-blue-500/10 backdrop-blur-sm border border-blue-400/20 rounded-lg">
                        <h3 className="text-sm font-medium text-blue-200 mb-2">Uploaded Files:</h3>
                        <ul className="space-y-1">
                          {uploadedFiles.map((filename, index) => (
                            <li key={index} className="text-xs text-blue-100/80 flex items-center gap-2">
                              <svg className="w-3 h-3 text-green-400" fill="currentColor" viewBox="0 0 20 20">
                                <path
                                  fillRule="evenodd"
                                  d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z"
                                  clipRule="evenodd"
                                />
                              </svg>
                              {filename}
                            </li>
                          ))}
                        </ul>
                      </div>
                    )}
                  </div>
                </div>
              </div>
            </motion.div>
          </motion.div>
        )}
      </AnimatePresence>

      {/* Similar Regions Modal */}
      <AnimatePresence>
        {showSimilarRegions && <SimilarRegions result={analysisResult} onClose={() => setShowSimilarRegions(false)} />}
      </AnimatePresence>
    </div>
  );
}
