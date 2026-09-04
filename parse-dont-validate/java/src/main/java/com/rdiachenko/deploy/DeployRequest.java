package com.rdiachenko.deploy;

import jakarta.validation.constraints.Pattern;
import jakarta.validation.constraints.Positive;

/**
 * The request shape from the post's "Validation in Java" section.
 *
 * <p>Both string constraints use {@link Pattern}, which is part of standard
 * Jakarta Bean Validation. There is no built-in "one of these values"
 * constraint: {@code @ValidEnum} has been proposed
 * (jakartaee/validation#229) but is not in the specification, and Hibernate
 * Validator does not add one either. Alternation in a regex covers it without
 * any custom code.
 *
 * <p>The annotations describe what a valid request looks like, but they do not
 * change the type. {@code service()} returns a {@code String} before validation
 * and a {@code String} after, so a checked request and an unchecked one are
 * indistinguishable to the compiler and to a reviewer.
 */
public record DeployRequest(
        @Pattern(regexp = "[a-z0-9-]{3,30}") String service,
        @Pattern(regexp = "dev|staging|production") String environment,
        @Positive int replicas
) {}
