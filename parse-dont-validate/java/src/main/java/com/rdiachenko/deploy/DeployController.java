package com.rdiachenko.deploy;

import jakarta.validation.Valid;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RestController;

@RestController
public class DeployController {

    private final DeployService deployService;

    public DeployController(DeployService deployService) {
        this.deployService = deployService;
    }

    @PostMapping("/deploys")
    public ResponseEntity<?> deploy(@Valid @RequestBody DeployRequest req) {
        deployService.submit(req);
        return ResponseEntity.accepted().build();
    }
}
