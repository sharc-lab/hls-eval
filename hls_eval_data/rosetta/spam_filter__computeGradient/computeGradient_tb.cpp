#include <iostream>

#include "computeGradient.h"

int main() {
    float feature_f[NUM_FEATURES];
    float grad_expected_f[NUM_FEATURES];
    float scale_f = 0.5f; // Example scale factor

    // Initialize input features with some test values
    for (int i = 0; i < NUM_FEATURES; i++) {
        feature_f[i] = 2.0f / (i + 1); // Example: decreasing values
        grad_expected_f[i] = scale_f * feature_f[i];
    }

    FeatureType grad[NUM_FEATURES];
    DataType feature[NUM_FEATURES];
    FeatureType scale = FeatureType(scale_f);

    for (int i = 0; i < NUM_FEATURES; i++) {
        feature[i] = DataType(feature_f[i]);
    }

    // Call the computeGradient function
    computeGradient(grad, feature, scale);

    // Compare results
    for (int i = 0; i < NUM_FEATURES; i++) {
        float grad_f = float(grad[i]);
        if (std::abs(grad_f - grad_expected_f[i]) > 1e-3) {
            std::cout << "Test failed at index " << i
                      << "! Expected: " << grad_expected_f[i]
                      << ", Got: " << grad_f << std::endl;
            return 1;
        }
    }

    std::cout << "Test passed!" << std::endl;
    return 0;
}
