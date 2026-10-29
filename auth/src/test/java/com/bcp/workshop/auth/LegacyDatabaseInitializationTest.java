package com.bcp.workshop.auth;

import io.quarkus.test.junit.QuarkusMock;
import io.quarkus.test.junit.QuarkusTest;
import jakarta.inject.Inject;
import org.junit.jupiter.api.Test;

import java.sql.Connection;
import java.sql.SQLException;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertThrows;

@QuarkusTest
class LegacyDatabaseInitializationTest {
    @Inject
    LegacyDatabase database;

    @Test
    void initializeFailsWhenPasswordMigrationFails() {
        QuarkusMock.installMockForType(new LegacyDatabase() {
            @Override
            void migratePlaintextPasswords(Connection connection) throws SQLException {
                throw new SQLException("migration fixture failure");
            }
        }, LegacyDatabase.class);

        IllegalStateException error = assertThrows(IllegalStateException.class, database::initialize);

        assertEquals("migration fixture failure", error.getCause().getMessage());
    }
}
