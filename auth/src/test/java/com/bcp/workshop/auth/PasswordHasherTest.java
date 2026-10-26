package com.bcp.workshop.auth;

import org.junit.jupiter.api.Test;

import java.util.Base64;

import static org.junit.jupiter.api.Assertions.assertFalse;
import static org.junit.jupiter.api.Assertions.assertNotEquals;
import static org.junit.jupiter.api.Assertions.assertTrue;

class PasswordHasherTest {
    private final PasswordHasher passwordHasher = new PasswordHasher();

    @Test
    void usesDistinctSaltsAndVerifiesOnlyMatchingPassword() {
        String firstHash = passwordHasher.hash("Workshop123!");
        String secondHash = passwordHasher.hash("Workshop123!");

        assertNotEquals(firstHash, secondHash);
        assertTrue(passwordHasher.matches("Workshop123!", firstHash));
        assertFalse(passwordHasher.matches("wrong-password", firstHash));
    }

    @Test
    void rejectsMalformedEncodedPassword() {
        assertFalse(passwordHasher.matches("Workshop123!", "not-a-password-hash"));
        assertFalse(passwordHasher.isEncoded("not-a-password-hash"));
        assertFalse(passwordHasher.matches("Workshop123!", null));
        assertFalse(passwordHasher.matches("Workshop123!", "$pbkdf2-sha256$1$salt$hash"));
        assertFalse(passwordHasher.matches("Workshop123!", "$pbkdf2-sha256$600000$!$!"));

        String salt = Base64.getUrlEncoder().withoutPadding().encodeToString(new byte[16]);
        assertFalse(passwordHasher.matches("Workshop123!", "$pbkdf2-sha256$600000$" + salt + "$AA"));
    }
}
