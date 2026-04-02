using Microsoft.EntityFrameworkCore;
using Microsoft.Extensions.DependencyInjection;
using SimuladorClinico.Infrastructure.Persistence;

namespace SimuladorClinico.Infrastructure;

public static class DependencyInjection
{
    public static IServiceCollection AddInfrastructure(
        this IServiceCollection services,
        Action<DbContextOptionsBuilder> configureDbContext)
    {
        services.AddDbContext<SimuladorClinicoDbContext>(configureDbContext);
        return services;
    }
}
