#include <iostream>

#include "dotProduct.h"

int main() {
    float param_f[NUM_FEATURES];
    float feature_f[NUM_FEATURES];
    float expected_result_f = 0;

    // Initialize inputs with some test values
    for (int i = 0; i < NUM_FEATURES; i++) {
        param_f[i] = 1.0f / (i + 1);    // Example: decreasing values
        feature_f[i] = -2.0f / (i + 1); // Example: decreasing values
        expected_result_f += param_f[i] * feature_f[i];
    }

    FeatureType param[NUM_FEATURES];
    DataType feature[NUM_FEATURES];

    for (int i = 0; i < NUM_FEATURES; i++) {
        param[i] = FeatureType(param_f[i]);
        feature[i] = DataType(feature_f[i]);
    }

    // Call the dotProduct function
    FeatureType result = dotProduct(param, feature);

    // Convert result back to float for comparison
    float result_f = float(result);

    // Compare the result with expected output (allowing for small numerical
    // errors)
    if (std::abs(result_f - expected_result_f) > 1e-2) {
        std::cout << "Test failed! Expected: " << expected_result_f
                  << ", Got: " << result_f << std::endl;
        return 1;
    }

    std::cout << "Test passed!" << std::endl;
    return 0;
}
