#include"cfd_step_factor.h"

/* These helpers return `fixed_t` (ap_fixed<32,16>, a C++ class type) by
 * value, which is ill-formed under C linkage ("has C-linkage specified,
 * but returns user-defined type ... which is incompatible with C"). They
 * are only ever called from within this translation unit, so they don't
 * need C linkage; only the top-level kernel entry point below does. */
inline void compute_velocity(fixed_t& density, float3& momentum, float3& velocity)
{
    velocity.x = momentum.x / density;
    velocity.y = momentum.y / density;
    velocity.z = momentum.z / density;
}

inline fixed_t compute_speed_sqd(float3& velocity)
{
    return velocity.x*velocity.x + velocity.y*velocity.y + velocity.z*velocity.z;
}

inline fixed_t compute_pressure(fixed_t& density, fixed_t& density_energy, fixed_t& speed_sqd)
{
    return (fixed_t(GAMMA) - fixed_t(1.0f))*(density_energy - fixed_t(0.5f)*density*speed_sqd);
}

inline fixed_t compute_speed_of_sound(fixed_t& density, fixed_t& pressure)
{
    return fixed_t(sqrt((double)(fixed_t(GAMMA)*pressure / density)));
}

extern "C" {

void workload(fixed_t result[SIZE], fixed_t variables[SIZE * NVAR], fixed_t areas[SIZE])
{

    #pragma HLS INTERFACE m_axi port=result offset=slave bundle=result1
    #pragma HLS INTERFACE m_axi port=variables offset=slave bundle=variables1
    #pragma HLS INTERFACE m_axi port=areas offset=slave bundle=areas1
    
    #pragma HLS INTERFACE s_axilite port=result bundle=control
    #pragma HLS INTERFACE s_axilite port=variables bundle=control
    #pragma HLS INTERFACE s_axilite port=areas bundle=control
    
    #pragma HLS INTERFACE s_axilite port=return bundle=control

    for (int i = 0; i < SIZE; i++)
    {
        fixed_t density = variables[NVAR*i + VAR_DENSITY];

        float3 momentum;
        momentum.x = variables[NVAR*i + (VAR_MOMENTUM + 0)];
        momentum.y = variables[NVAR*i + (VAR_MOMENTUM + 1)];
        momentum.z = variables[NVAR*i + (VAR_MOMENTUM + 2)];

        fixed_t density_energy = variables[NVAR*i + VAR_DENSITY_ENERGY];
        float3 velocity;       compute_velocity(density, momentum, velocity);
        fixed_t speed_sqd      = compute_speed_sqd(velocity);
        fixed_t pressure       = compute_pressure(density, density_energy, speed_sqd);
        fixed_t speed_of_sound = compute_speed_of_sound(density, pressure);

        fixed_t sqrt_areas = fixed_t(sqrt((double)areas[i]));
        fixed_t sqrt_speed_sqd = fixed_t(sqrt((double)speed_sqd));
        result[i] = fixed_t(0.5f) / (sqrt_areas * (sqrt_speed_sqd + speed_of_sound));
    }

    return;
}

}

