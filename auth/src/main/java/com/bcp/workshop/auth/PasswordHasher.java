package com.bcp.workshop.auth;

import jakarta.enterprise.context.ApplicationScoped;

import javax.crypto.SecretKeyFactory;
import javax.crypto.spec.PBEKeySpec;
import java.security.GeneralSecurityException;
import java.security.MessageDigest;
import java.security.SecureRandom;
import java.util.Arrays;
import java.util.Base64;
import java.util.Objects;

@ApplicationScoped
public class PasswordHasher {
    private static final String HASH_ALGORITHM_ID = "pbkdf2-sha256";
    private static final String HASH_PREFIX = "$" + HASH_ALGORITHM_ID + "$";
    private static final String KEY_DERIVATION_ALGORITHM = "PBKDF2WithHmacSHA256";
    private static final int ITERATION_COUNT = 600_000;
    private static final int SALT_LENGTH_BYTES = 16;
    private static final int KEY_LENGTH_BITS = 256;

    private final SecureRandom secureRandom = new SecureRandom();

    public String hash(String password) {
        Objects.requireNonNull(password, "password");
        byte[] salt = new byte[SALT_LENGTH_BYTES];
        secureRandom.nextBytes(salt);

        byte[] derivedKey = derive(password, salt);
        try {
            return HASH_PREFIX + ITERATION_COUNT + "$"
                    + Base64.getUrlEncoder().withoutPadding().encodeToString(salt) + "$"
                    + Base64.getUrlEncoder().withoutPadding().encodeToString(derivedKey);
        } finally {
            Arrays.fill(derivedKey, (byte) 0);
        }
    }

    public boolean matches(String password, String encodedPassword) {
        Objects.requireNonNull(password, "password");
        EncodedHash encodedHash = parse(encodedPassword);
        if (encodedHash == null) {
            return false;
        }

        byte[] candidateKey = derive(password, encodedHash.salt());
        try {
            return MessageDigest.isEqual(candidateKey, encodedHash.derivedKey());
        } finally {
            Arrays.fill(candidateKey, (byte) 0);
            Arrays.fill(encodedHash.salt(), (byte) 0);
            Arrays.fill(encodedHash.derivedKey(), (byte) 0);
        }
    }

    boolean isEncoded(String value) {
        EncodedHash encodedHash = parse(value);
        if (encodedHash == null) {
            return false;
        }
        Arrays.fill(encodedHash.salt(), (byte) 0);
        Arrays.fill(encodedHash.derivedKey(), (byte) 0);
        return true;
    }

    private byte[] derive(String password, byte[] salt) {
        char[] passwordCharacters = password.toCharArray();
        PBEKeySpec keySpec = new PBEKeySpec(passwordCharacters, salt, ITERATION_COUNT, KEY_LENGTH_BITS);
        try {
            SecretKeyFactory keyFactory = SecretKeyFactory.getInstance(KEY_DERIVATION_ALGORITHM);
            return keyFactory.generateSecret(keySpec).getEncoded();
        } catch (GeneralSecurityException error) {
            throw new IllegalStateException("Password hashing is unavailable", error);
        } finally {
            keySpec.clearPassword();
            Arrays.fill(passwordCharacters, '\0');
        }
    }

    private EncodedHash parse(String encodedPassword) {
        if (encodedPassword == null) {
            return null;
        }

        String[] parts = encodedPassword.split("\\$", -1);
        if (parts.length != 5 || !parts[0].isEmpty() || !HASH_ALGORITHM_ID.equals(parts[1])) {
            return null;
        }

        try {
            if (Integer.parseInt(parts[2]) != ITERATION_COUNT) {
                return null;
            }
            byte[] salt = Base64.getUrlDecoder().decode(parts[3]);
            byte[] derivedKey = Base64.getUrlDecoder().decode(parts[4]);
            if (salt.length != SALT_LENGTH_BYTES || derivedKey.length != KEY_LENGTH_BITS / Byte.SIZE) {
                Arrays.fill(salt, (byte) 0);
                Arrays.fill(derivedKey, (byte) 0);
                return null;
            }
            return new EncodedHash(salt, derivedKey);
        } catch (IllegalArgumentException error) {
            return null;
        }
    }

    private record EncodedHash(byte[] salt, byte[] derivedKey) {}
}
