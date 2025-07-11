import { NextRequest, NextResponse } from "next/server";

// Security Configuration
const MAX_FILES = 50;
const MAX_FILE_SIZE = 1 * 1024 * 1024; // 1MB
const MAX_TOTAL_SIZE = 5 * 1024 * 1024; // 5MB
const REQUEST_TIMEOUT = 310000; // 5 minutes + buffer

// Simple in-memory rate limiting (for basic protection)
const requestCounts = new Map();
const RATE_LIMIT_WINDOW = 60000; // 1 minute
const RATE_LIMIT_MAX = 10; // 10 requests per minute

function getClientIP(request) {
  // Try to get real IP from headers
  const forwarded = request.headers.get("x-forwarded-for");
  if (forwarded) {
    return forwarded.split(",")[0].trim();
  }

  const realIP = request.headers.get("x-real-ip");
  if (realIP) {
    return realIP;
  }

  // Fallback (may not be accurate in production)
  return request.ip || "unknown";
}

function isRateLimited(clientIP) {
  const now = Date.now();
  const clientRequests = requestCounts.get(clientIP) || [];

  // Remove old requests outside the window
  const recentRequests = clientRequests.filter((time) => now - time < RATE_LIMIT_WINDOW);

  if (recentRequests.length >= RATE_LIMIT_MAX) {
    return true;
  }

  // Add current request
  recentRequests.push(now);
  requestCounts.set(clientIP, recentRequests);

  return false;
}

export async function POST(request) {
  const clientIP = getClientIP(request);

  try {
    // Rate limiting check
    if (isRateLimited(clientIP)) {
      console.warn(`Rate limit exceeded for IP: ${clientIP}`);
      return NextResponse.json({ error: "Rate limit exceeded. Please wait before making another request." }, { status: 429 });
    }

    // Parse form data with size validation
    const formData = await request.formData();
    const files = formData.getAll("files");

    // Validate number of files
    if (files.length > MAX_FILES) {
      return NextResponse.json({ error: `Too many files. Maximum ${MAX_FILES} files allowed.` }, { status: 400 });
    }

    // Validate file sizes
    let totalSize = 0;
    for (const file of files) {
      if (file.size > MAX_FILE_SIZE) {
        return NextResponse.json(
          { error: `File "${file.name}" is too large. Maximum ${MAX_FILE_SIZE / (1024 * 1024)}MB per file.` },
          { status: 413 }
        );
      }
      totalSize += file.size;
    }

    if (totalSize > MAX_TOTAL_SIZE) {
      return NextResponse.json({ error: `Total upload size too large. Maximum ${MAX_TOTAL_SIZE / (1024 * 1024)}MB allowed.` }, { status: 413 });
    }

    console.log(`Processing request from ${clientIP} with ${files.length} files (${Math.round(totalSize / 1024)}KB total)`);

    const baseUrl = process.env.NODE_ENV === "development" ? "http://127.0.0.1:8000" : "https://codebase-refactor-detection-api.vercel.app";

    // Create AbortController for timeout
    const controller = new AbortController();
    const timeoutId = setTimeout(() => controller.abort(), REQUEST_TIMEOUT);

    try {
      // Forward the form data to the FastAPI server
      const response = await fetch(`${baseUrl}/refactor`, {
        method: "POST",
        body: formData,
        signal: controller.signal,
        headers: {
          // Forward client IP to backend for logging
          "X-Forwarded-For": clientIP,
        },
      });

      clearTimeout(timeoutId);

      if (!response.ok) {
        const errorText = await response.text();
        console.error(`FastAPI error (${response.status}):`, errorText);

        // Return appropriate error based on status
        if (response.status === 429) {
          return NextResponse.json({ error: "Server is busy. Please try again later." }, { status: 429 });
        } else if (response.status === 413) {
          return NextResponse.json({ error: "Upload too large. Please reduce file size or number of files." }, { status: 413 });
        } else if (response.status === 408) {
          return NextResponse.json({ error: "Analysis took too long. Please try with a smaller codebase." }, { status: 408 });
        } else {
          return NextResponse.json({ error: "Analysis failed. Please try again." }, { status: response.status });
        }
      }

      const result = await response.json();
      console.log(`Analysis completed for ${clientIP}: ${result.total_regions_found || 0} regions found`);
      return NextResponse.json(result);
    } catch (fetchError) {
      clearTimeout(timeoutId);

      if (fetchError.name === "AbortError") {
        console.error(`Request timeout for ${clientIP}`);
        return NextResponse.json({ error: "Request timed out. Please try with a smaller codebase." }, { status: 408 });
      }

      throw fetchError;
    }
  } catch (error) {
    console.error(`Upload error for ${clientIP}:`, error.message);

    // Don't leak internal error details
    return NextResponse.json({ error: "Upload failed. Please check your files and try again." }, { status: 500 });
  }
}
