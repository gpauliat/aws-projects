import { Amplify } from "aws-amplify";
import {
  signUp as amplifySignUp,
  signIn as amplifySignIn,
  signOut as amplifySignOut,
  resetPassword as amplifyResetPassword,
  confirmResetPassword as amplifyConfirmResetPassword,
  confirmSignUp as amplifyConfirmSignUp,
  getCurrentUser as amplifyGetCurrentUser,
  fetchUserAttributes,
  AuthError,
} from "aws-amplify/auth";
import type {
  SignUpOutput,
  SignInOutput,
  ResetPasswordOutput,
  GetCurrentUserOutput,
} from "aws-amplify/auth";

// ─── Amplify Configuration ──────────────────────────────────────────────────

Amplify.configure({
  Auth: {
    Cognito: {
      userPoolId: import.meta.env.VITE_COGNITO_USER_POOL_ID ?? "",
      userPoolClientId: import.meta.env.VITE_COGNITO_CLIENT_ID ?? "",
    },
  },
});

// ─── Generic error message for login failures (Requirement 1.3) ─────────────

const GENERIC_LOGIN_ERROR =
  "The email or password you entered is incorrect.";

// ─── Types ───────────────────────────────────────────────────────────────────

export interface AuthUser {
  userId: string;
  email: string;
}

// ─── Auth Functions ──────────────────────────────────────────────────────────

/**
 * Register a new user with email and password.
 * Returns the sign-up output which includes confirmation status.
 *
 * Requirement 1.1: Create a new user account
 */
export async function signUp(
  email: string,
  password: string
): Promise<SignUpOutput> {
  try {
    const result = await amplifySignUp({
      username: email,
      password,
      options: {
        userAttributes: {
          email,
        },
      },
    });
    return result;
  } catch (error) {
    if (error instanceof AuthError) {
      throw new Error(error.message);
    }
    throw new Error("An unexpected error occurred during registration.");
  }
}

/**
 * Confirm a user's sign-up with the verification code sent to their email.
 *
 * Requirement 1.1: Complete the registration confirmation flow
 */
export async function confirmSignUp(
  email: string,
  confirmationCode: string
): Promise<void> {
  try {
    await amplifyConfirmSignUp({
      username: email,
      confirmationCode,
    });
  } catch (error) {
    if (error instanceof AuthError) {
      throw new Error(error.message);
    }
    throw new Error("An unexpected error occurred during confirmation.");
  }
}

/**
 * Sign in with email and password.
 * Returns a generic error message on failure to avoid revealing which credential
 * is incorrect (Requirement 1.3).
 * Surfaces "UserNotConfirmedException" so the UI can redirect to confirmation.
 *
 * Requirement 1.2: Authenticate and grant access
 */
export async function signIn(
  email: string,
  password: string
): Promise<SignInOutput> {
  try {
    const result = await amplifySignIn({
      username: email,
      password,
    });
    return result;
  } catch (error) {
    // Log the real error for debugging
    console.error("[Auth] signIn error:", error);
    if (error instanceof AuthError) {
      console.error("[Auth] AuthError name:", error.name, "message:", error.message);
    }

    // If there's already a sign-in session in progress, clear it and retry
    if (
      error instanceof AuthError &&
      error.name === "UserAlreadyAuthenticatedException"
    ) {
      await amplifySignOut();
      const result = await amplifySignIn({
        username: email,
        password,
      });
      return result;
    }
    // Surface confirmation errors so the UI can handle them
    if (
      error instanceof AuthError &&
      error.name === "UserNotConfirmedException"
    ) {
      throw new Error("USER_NOT_CONFIRMED");
    }
    // Requirement 1.3: Do not reveal which credential is wrong
    throw new Error(GENERIC_LOGIN_ERROR);
  }
}

/**
 * Sign out the current user and clear the session.
 */
export async function signOut(): Promise<void> {
  try {
    await amplifySignOut();
  } catch (error) {
    if (error instanceof AuthError) {
      throw new Error(error.message);
    }
    throw new Error("An unexpected error occurred during sign out.");
  }
}

/**
 * Initiate a password reset by sending a verification code to the user's email.
 *
 * Requirement 1.4: Send a password reset link/code
 */
export async function resetPassword(
  email: string
): Promise<ResetPasswordOutput> {
  try {
    const result = await amplifyResetPassword({ username: email });
    return result;
  } catch (error) {
    if (error instanceof AuthError) {
      throw new Error(error.message);
    }
    throw new Error(
      "An unexpected error occurred while requesting a password reset."
    );
  }
}

/**
 * Complete the password reset by submitting the verification code and new password.
 *
 * Requirement 1.4: Handle new password submission
 */
export async function confirmPasswordReset(
  email: string,
  confirmationCode: string,
  newPassword: string
): Promise<void> {
  try {
    await amplifyConfirmResetPassword({
      username: email,
      confirmationCode,
      newPassword,
    });
  } catch (error) {
    if (error instanceof AuthError) {
      throw new Error(error.message);
    }
    throw new Error(
      "An unexpected error occurred while resetting your password."
    );
  }
}

/**
 * Get the currently authenticated user's info.
 * Returns null if no user is signed in.
 */
export async function getCurrentUser(): Promise<AuthUser | null> {
  try {
    const user: GetCurrentUserOutput = await amplifyGetCurrentUser();
    const attributes = await fetchUserAttributes();
    return {
      userId: user.userId,
      email: attributes.email ?? "",
    };
  } catch {
    // No authenticated user
    return null;
  }
}
