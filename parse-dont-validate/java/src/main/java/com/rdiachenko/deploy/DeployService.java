package com.rdiachenko.deploy;

import org.springframework.stereotype.Service;

@Service
public class DeployService {

    /**
     * Accepts a raw {@link DeployRequest}. Nothing in this signature records
     * that {@code @Valid} ran at the controller, so a Kafka consumer or a batch
     * import calling this method directly gets no guarantee at all.
     */
    public void submit(DeployRequest req) {
        // A real implementation would re-parse `replicas` here, or trust that
        // someone upstream checked it.
        System.out.printf("submitting %s to %s x%d%n",
                req.service(), req.environment(), req.replicas());
    }
}
