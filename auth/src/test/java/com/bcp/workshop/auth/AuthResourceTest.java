package com.bcp.workshop.auth;

import io.quarkus.test.junit.QuarkusMock;
import io.quarkus.test.junit.QuarkusTest;
import jakarta.inject.Inject;
import org.junit.jupiter.api.Test;

import java.sql.Connection;
import java.sql.DriverManager;
import java.sql.PreparedStatement;
import java.sql.ResultSet;
import java.sql.SQLException;
import java.util.UUID;

import static io.restassured.RestAssured.given;
import static org.hamcrest.CoreMatchers.is;
import static org.hamcrest.Matchers.isEmptyOrNullString;
import static org.hamcrest.Matchers.notNullValue;
import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertNotEquals;
import static org.junit.jupiter.api.Assertions.assertTrue;

@QuarkusTest
class AuthResourceTest {
    private static final String DB_URL = System.getenv().getOrDefault("AUTH_DB_URL", "jdbc:sqlite:./data/workshop.db");
    private static final String QUOTED_USERNAME_PASSWORD = "FixturePassword123!";
    private static final String MIGRATION_PASSWORD = "LegacyFixture123!";

    @Inject
    LegacyDatabase database;

    @Inject
    PasswordHasher passwordHasher;

    @Test
    void logsInWithWorkshopUser() {
        given()
                .contentType("application/json")
                .body("{\"username\":\"student\",\"password\":\"Workshop123!\",\"client\":\"angular-workshop\"}")
                .when().post("/auth/login")
                .then()
                .statusCode(200)
                .body("user.username", is("student"))
                .body("user.displayName", is("Workshop Student"))
                .body("user.role", is("STUDENT"))
                .body("token", notNullValue())
                .body("expiresIn", is(3600))
                .body("debug", is("authenticated-with-legacy-flow"));
    }

    @Test
    void logsInWhenOptionalClientIsOmitted() {
        given()
                .contentType("application/json")
                .body("{\"username\":\"student\",\"password\":\"Workshop123!\"}")
                .when().post("/auth/login")
                .then()
                .statusCode(200)
                .body("user.username", is("student"));
    }

    @Test
    void rejectsNullRequest() {
        given()
                .contentType("application/json")
                .body("null")
                .when().post("/auth/login")
                .then()
                .statusCode(400)
                .body("message", is("Request is null"));
    }

    @Test
    void rejectsEmptyRequestBody() {
        given()
                .contentType("application/json")
                .body("")
                .when().post("/auth/login")
                .then()
                .statusCode(400)
                .body("message", is("Request is null"));
    }

    @Test
    void rejectsMalformedJson() {
        given()
                .contentType("application/json")
                .body("{")
                .when().post("/auth/login")
                .then()
                .statusCode(400)
                .body(isEmptyOrNullString());
    }

    @Test
    void rejectsMissingUsername() {
        given()
                .contentType("application/json")
                .body("{\"password\":\"Workshop123!\"}")
                .when().post("/auth/login")
                .then()
                .statusCode(400)
                .body("message", is("Username is required"));
    }

    @Test
    void rejectsBlankUsername() {
        given()
                .contentType("application/json")
                .body("{\"username\":\"   \",\"password\":\"Workshop123!\"}")
                .when().post("/auth/login")
                .then()
                .statusCode(400)
                .body("message", is("Username is required"));
    }

    @Test
    void rejectsMissingPassword() {
        given()
                .contentType("application/json")
                .body("{\"username\":\"student\"}")
                .when().post("/auth/login")
                .then()
                .statusCode(400)
                .body("message", is("Password is required"));
    }

    @Test
    void rejectsBlankPassword() {
        given()
                .contentType("application/json")
                .body("{\"username\":\"student\",\"password\":\"   \"}")
                .when().post("/auth/login")
                .then()
                .statusCode(400)
                .body("message", is("Password is required"));
    }

    @Test
    void rejectsIncorrectPassword() {
        given()
                .contentType("application/json")
                .body("{\"username\":\"student\",\"password\":\"incorrecta\"}")
                .when().post("/auth/login")
                .then()
                .statusCode(401)
                .body("message", is("Invalid user student or password"));
    }

    @Test
    void rejectsUnknownUsername() {
        given()
                .contentType("application/json")
                .body("{\"username\":\"missing-user\",\"password\":\"FixturePassword123!\"}")
                .when().post("/auth/login")
                .then()
                .statusCode(401)
                .body("message", is("Invalid user missing-user or password"));
    }

    @Test
    void rejectsUnsupportedHttpMethod() {
        given()
                .when().get("/auth/login")
                .then()
                .statusCode(405)
                .body(isEmptyOrNullString());
    }

    @Test
    void rejectsUnsupportedAcceptType() {
        given()
                .accept("text/plain")
                .contentType("application/json")
                .body("{\"username\":\"student\",\"password\":\"Workshop123!\"}")
                .when().post("/auth/login")
                .then()
                .statusCode(406)
                .body(isEmptyOrNullString());
    }

    @Test
    void rejectsUnsupportedRequestContentType() {
        given()
                .contentType("text/plain")
                .body("{\"username\":\"student\",\"password\":\"Workshop123!\"}")
                .when().post("/auth/login")
                .then()
                .statusCode(415)
                .body(isEmptyOrNullString());
    }

    @Test
    void returnsObservedInternalErrorResponseWhenUserRecordIsMalformed() {
        QuarkusMock.installMockForType(new LegacyDatabase() {
            @Override
            public UserRecord findByCredentials(String username, String password) {
                return new UserRecord(1, username, null, "STUDENT");
            }
        }, LegacyDatabase.class);

        given()
                .contentType("application/json")
                .body("{\"username\":\"student\",\"password\":\"Workshop123!\"}")
                .when().post("/auth/login")
                .then()
                .statusCode(500)
                .body("exception", is("java.lang.NullPointerException"))
                .body("message", is("Unknown error"));
    }

    @Test
    void logsInWithUsernameContainingAQuote() throws SQLException {
        String username = "quoted-user-" + UUID.randomUUID() + "'fixture";
        insertPasswordFixture(username, passwordHasher.hash(QUOTED_USERNAME_PASSWORD));
        try {
            given()
                    .contentType("application/json")
                    .body("{\"username\":\"" + username + "\",\"password\":\"" + QUOTED_USERNAME_PASSWORD + "\"}")
                    .when().post("/auth/login")
                    .then()
                    .statusCode(200)
                    .body("user.username", is(username))
                    .body("token", notNullValue());
        } finally {
            removePasswordFixture(username);
        }
    }

    @Test
    void storesSeedPasswordAsHash() throws SQLException {
        database.initialize();
        String storedPassword = readStoredPassword("student");

        assertNotEquals("Workshop123!", storedPassword);
        assertTrue(passwordHasher.matches("Workshop123!", storedPassword));
    }

    @Test
    void migratesExistingPlaintextPasswordsIdempotently() throws SQLException {
        String username = "legacy-plaintext-fixture-" + UUID.randomUUID();
        insertPasswordFixture(username, MIGRATION_PASSWORD);
        try {
            try (Connection connection = DriverManager.getConnection(DB_URL)) {
                database.migratePlaintextPasswords(connection);
            }
            String migratedPassword = readStoredPassword(username);
            assertNotEquals(MIGRATION_PASSWORD, migratedPassword);
            assertTrue(passwordHasher.matches(MIGRATION_PASSWORD, migratedPassword));

            try (Connection connection = DriverManager.getConnection(DB_URL)) {
                database.migratePlaintextPasswords(connection);
            }
            assertEquals(migratedPassword, readStoredPassword(username));
        } finally {
            removePasswordFixture(username);
        }
    }

    @Test
    void seedsMissingUserWithHashedPassword() throws SQLException {
        String username = "seed-fixture-" + UUID.randomUUID();
        String password = "SeedFixture123!";
        try {
            try (Connection connection = DriverManager.getConnection(DB_URL)) {
                database.seedUserIfMissing(connection, username, password, "Seed Fixture", "STUDENT");
            }
            assertTrue(passwordHasher.matches(password, readStoredPassword(username)));
        } finally {
            removePasswordFixture(username);
        }
    }

    private void insertPasswordFixture(String username, String password) throws SQLException {
        String sql = "INSERT OR REPLACE INTO legacy_users(username,password,display_name,role) VALUES (?, ?, ?, ?)";
        try (Connection connection = DriverManager.getConnection(DB_URL);
             PreparedStatement statement = connection.prepareStatement(sql)) {
            statement.setString(1, username);
            statement.setString(2, password);
            statement.setString(3, "Quoted Fixture");
            statement.setString(4, "STUDENT");
            statement.executeUpdate();
        }
    }

    private String readStoredPassword(String username) throws SQLException {
        try (Connection connection = DriverManager.getConnection(DB_URL);
             PreparedStatement statement = connection.prepareStatement(
                     "SELECT password FROM legacy_users WHERE username = ?")) {
            statement.setString(1, username);
            try (ResultSet result = statement.executeQuery()) {
                assertTrue(result.next());
                return result.getString("password");
            }
        }
    }

    private void removePasswordFixture(String username) throws SQLException {
        try (Connection connection = DriverManager.getConnection(DB_URL);
             PreparedStatement statement = connection.prepareStatement("DELETE FROM legacy_users WHERE username = ?")) {
            statement.setString(1, username);
            statement.executeUpdate();
        }
    }
}
