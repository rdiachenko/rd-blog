package com.rdiachenko.deploy;

import jakarta.validation.ConstraintViolation;
import jakarta.validation.Validation;
import jakarta.validation.Validator;
import jakarta.validation.ValidatorFactory;
import org.junit.jupiter.api.AfterAll;
import org.junit.jupiter.api.BeforeAll;
import org.junit.jupiter.api.Test;

import java.util.Set;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertSame;
import static org.junit.jupiter.api.Assertions.assertTrue;

/**
 * The Java half of the post's argument, as assertions.
 */
class DeployRequestValidationTest {

    private static ValidatorFactory factory;
    private static Validator validator;

    @BeforeAll
    static void setUp() {
        factory = Validation.buildDefaultValidatorFactory();
        validator = factory.getValidator();
    }

    @AfterAll
    static void tearDown() {
        factory.close();
    }

    @Test
    void invalidRequestsAreReported() {
        var bad = new DeployRequest("Not A Service", "qa", 0);

        Set<ConstraintViolation<DeployRequest>> violations = validator.validate(bad);

        assertEquals(3, violations.size());
    }

    /**
     * The load-bearing test. Validation succeeds, and the only thing it hands
     * back is an empty set. Success produces no new knowledge, which is the
     * Java equivalent of {@code Result<(), E>} in the Rust version.
     */
    @Test
    void successfulValidationProducesNothing() {
        var good = new DeployRequest("checkout-api", "production", 3);

        Set<ConstraintViolation<DeployRequest>> violations = validator.validate(good);

        assertTrue(violations.isEmpty());
    }

    /**
     * And the request is the same object, of the same type, before and after.
     * There is no "validated DeployRequest" type to pass downstream, so every
     * function taking a DeployRequest has to trust that someone called the
     * validator first.
     */
    @Test
    void validationDoesNotChangeTheValueOrItsType() {
        var req = new DeployRequest("checkout-api", "production", 3);

        String serviceBefore = req.service();
        validator.validate(req);
        String serviceAfter = req.service();

        assertSame(serviceBefore, serviceAfter);
        assertEquals(String.class, req.service().getClass());
    }

    /**
     * The canonicalisation gap the Rust version closes by trimming and
     * lowercasing inside `ServiceName::parse`. Here the same logical service
     * fails the pattern, because nothing normalises the input.
     */
    @Test
    void nothingCanonicalisesTheInput() {
        var padded = new DeployRequest("  CHECKOUT-API  ", "production", 3);

        assertTrue(validator.validate(padded).size() > 0);
    }
}
