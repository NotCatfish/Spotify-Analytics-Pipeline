# 📜 THE YOLO AI MASTER PROTOCOL (STRICT ENFORCEMENT v5.1)

## 0. PRE-FLIGHT VERIFICATION
* **Mandatory Scan:** Read this file and `/master_readme/master_readme.md` before every task.
* **Verification:** State "Context Verified: [Feature Name]" before typing any code.
* **Continuity:** The file system is the only source of truth. Ignore past chat memory; follow existing naming patterns exactly.

## 1. TECH STACK MANDATE (NON-NEGOTIABLE)
* **Frontend:** Next.js (React), JavaScript (ES6+), Tailwind CSS. (No TypeScript).
* **Backend:** FastAPI (Python 3.10+).
* **Database:** PostgreSQL (via Supabase).
* **Services:** Supabase Auth & Storage.
* **Deployment:** Vercel (Serverless/Edge functions).

## 2. DYNAMIC VERTICAL SLICING
* **Feature Isolation:** Every feature lives in `/features/[FeatureName]/`.
* **Dynamic Generation:** Inside a feature folder, create ONLY the directories needed (e.g., `/frontend`, `/backend`, `/api`, `/db`). If a feature only needs a frontend, do not create a `/backend` folder.
* **Isolation:** Features are "bubbles." No logic or CSS leakage between feature folders.

## 3. THE MASTER DOCUMENTATION HUB (master_readme)
* **Global Tracker:** `/master_readme/master_readme.md` tracks overall progress, connection status, and high-level feature descriptions.
* **Atomic Feature Docs:** Use the structure: `/master_readme/features/[FeatureName]/[SubFeature]/`.
* **Dynamic Logging:** Create `.md` files dynamically (e.g., `frontend.md`, `backend.md`) within the sub-feature folder to document specific implementation logic as it is built.

## 4. THE SILENT OPERATOR (FILE SYSTEM ONLY)
* **Direct Write:** You must perform all code changes directly in the file system. 
* **No Chat Dumps:** Strictly forbidden from providing full code blocks or large snippets in the chat window unless explicitly asked for a "code review."
* **Full File Integrity:** When writing to a file, always write the complete, clean file to disk. Never use `// ... rest of code`.
* **Status Only:** In the chat, only provide a brief summary of which files were created/updated.

## 5. HUMAN-READABLE "KAIZEN" STANDARDS
* **Descriptive Naming:** `calculateKanjiStrokeOrder` > `calcK`.
* **Graceful Failure:** All external calls must have `try-catch` blocks. Show "Loading" or "Error" states in UI; never freeze.
* **Secret Management:** Use `.env` or `constants.js`. Zero hardcoding.

## 6. SCALABILITY & FINANCE
* **Serverless First:** Code must be stateless to scale from 0 to 1 million users.
* **Free-Tier Focus:** Prioritize logic that minimizes database hits to stay within free-tier limits.

## 7. AMBIGUITY PROTOCOL
* **Stop and Ask:** If a command conflicts with these rules or the architecture, STOP and ask for clarification. Do not guess.

## 8. DOCUMENTATION SYNC (SUMMARY OF PREVIOUS CHATS)
* **Strict Rule:** Upon adding, modifying, or enhancing any feature, strictly update the `summaryofpreviouschats.md` file using this logic:
  * **New Feature:** Append a precise explanation of its core functionality.
  * **Updated Feature:** Locate and delete the outdated entry. Overwrite/Replace it entirely with the current, most optimal explanation of how the revised feature operates.
* **Why:** This absolute system requirement ensures accurate context via an exact IF/THEN structure, preventing accidental appending instead of replacing. Using definitive action verbs (Overwrite/Replace) permits the deletion of old context, which prevents the summary file from bloating and consuming unnecessary tokens over time. This rule MUST be implemented after each prompt whenever something is updated or newly created.

## 9. EPHEMERAL SCRIPT HYGIENE (ZERO-TRASH POLICY)
* **One-Use Scripts:** Whenever you create a specific task script, database patcher, data-parsing snippet, or temporary SQL migration file (e.g., `patch_100.js`, `sanitize_tildes.sql`), you MUST permanently delete it from the file system the exact moment its execution/purpose is complete.
* **Purpose:** Maintain absolute cleanliness in the repository and prevent cluttering the codebase with dead, one-off utility files.

## 10. SECURITY & ARCHITECTURAL ADVISORY PROTOCOL
* **Pause and Advise:** Whenever the user requests an action, implementation, or design choice that poses a **security risk**, **privacy vulnerability**, or where there is a **significantly better or safer architectural pattern**, you must NOT immediately execute or commit code that introduces the vulnerability or sub-optimal pattern.
* **Proactive Explanation:** First proactively explain the specific risk (e.g., PII/email exposure, SQL injection, race condition) or better architectural approach with clear examples and alternatives.
* **Await Explicit Confirmation:** Strictly await the user's explicit confirmation or prompt before proceeding with either the recommended alternative or their original preference.

## 11. STRICT SECURITY NON-REGRESSION
* **Zero Security Compromise:** No matter how annoying or difficult a bug or feature implementation is, NEVER implement code that reduces the security level of the current site or program.
* **Forward Only:** Security must only increase or remain the same; it must never decrease under any circumstances (e.g., do not bypass authentication checks, verification steps, or expose admin APIs to standard flows for the sake of development convenience).

## 12. LOCAL DATABASE FIRST PROTOCOL
* **Strict Order of Operations:** In any project, always update the local database files (e.g., SQL seeds, schema files, local DB instances) FIRST. Only after the local files are updated, verified, and safely stored should you push or sync those updates to the cloud (e.g., Supabase production/remote database).
* **Why:** This ensures the local file system remains the indisputable source of truth and acts as an immediate fail-safe backup before any remote mutation.