package com.bcp.workshop.auth;

import io.quarkus.runtime.Startup;
import jakarta.annotation.PostConstruct;
import jakarta.enterprise.context.ApplicationScoped;
import jakarta.inject.Inject;

import java.io.IOException;
import java.nio.file.Files;
import java.nio.file.Path;
import java.sql.Connection;
import java.sql.DriverManager;
import java.sql.PreparedStatement;
import java.sql.ResultSet;
import java.sql.SQLException;
import java.sql.Statement;
import java.util.ArrayList;
import java.util.List;

@Startup
@ApplicationScoped
public class LegacyDatabase {
    private static final String DB_URL = System.getenv().getOrDefault("AUTH_DB_URL", "jdbc:sqlite:./data/workshop.db");

    @Inject
    PasswordHasher passwordHasher;

    @PostConstruct
    void initialize() {
        try {
            Files.createDirectories(Path.of("data"));
            try (Connection connection = DriverManager.getConnection(DB_URL); Statement statement = connection.createStatement()) {
                statement.executeUpdate("CREATE TABLE IF NOT EXISTS legacy_users (id INTEGER PRIMARY KEY AUTOINCREMENT, username TEXT UNIQUE, password TEXT NOT NULL, display_name TEXT NOT NULL, role TEXT NOT NULL)");
                migratePlaintextPasswords(connection);
                seedUserIfMissing(connection, "student", "Workshop123!", "Workshop Student", "STUDENT");
                seedUserIfMissing(connection, "trainer", "Trainer123!", "Workshop Trainer", "TRAINER");
            }
        } catch (IOException | SQLException error) {
            throw new IllegalStateException("Legacy database initialization failed", error);
        }
    }

    void migratePlaintextPasswords(Connection connection) throws SQLException {
        List<LegacyPassword> legacyPasswords = new ArrayList<>();
        try (PreparedStatement statement = connection.prepareStatement("SELECT id, password FROM legacy_users");
             ResultSet result = statement.executeQuery()) {
            while (result.next()) {
                String storedPassword = result.getString("password");
                if (!passwordHasher.isEncoded(storedPassword)) {
                    legacyPasswords.add(new LegacyPassword(result.getLong("id"), storedPassword));
                }
            }
        }

        try (PreparedStatement statement = connection.prepareStatement(
                "UPDATE legacy_users SET password = ? WHERE id = ?")) {
            for (LegacyPassword legacyPassword : legacyPasswords) {
                statement.setString(1, passwordHasher.hash(legacyPassword.password()));
                statement.setLong(2, legacyPassword.userId());
                statement.executeUpdate();
            }
        }
    }

    void seedUserIfMissing(Connection connection, String username, String password,
                           String displayName, String role) throws SQLException {
        try (PreparedStatement lookup = connection.prepareStatement(
                "SELECT 1 FROM legacy_users WHERE username = ?")) {
            lookup.setString(1, username);
            try (ResultSet result = lookup.executeQuery()) {
                if (result.next()) {
                    return;
                }
            }
        }

        String sql = "INSERT OR IGNORE INTO legacy_users(username,password,display_name,role) VALUES (?, ?, ?, ?)";
        try (PreparedStatement insert = connection.prepareStatement(sql)) {
            insert.setString(1, username);
            insert.setString(2, passwordHasher.hash(password));
            insert.setString(3, displayName);
            insert.setString(4, role);
            insert.executeUpdate();
        }
    }

    public UserRecord findByCredentials(String username, String password) {
        String sql = "SELECT id, username, password, display_name, role FROM legacy_users WHERE username = ?";
        try (Connection connection = DriverManager.getConnection(DB_URL);
             PreparedStatement statement = connection.prepareStatement(sql)) {
            statement.setString(1, username);
            try (ResultSet result = statement.executeQuery()) {
                if (!result.next() || !passwordHasher.matches(password, result.getString("password"))) {
                    return null;
                }
                return new UserRecord(result.getLong("id"), result.getString("username"), result.getString("display_name"), result.getString("role"));
            }
        } catch (Exception error) {
            error.printStackTrace();
        }
        return null;
    }

    private record LegacyPassword(long userId, String password) {}
}
