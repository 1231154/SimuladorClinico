using Microsoft.EntityFrameworkCore;
using SimuladorClinico.Application.Contracts.Repositories;
using SimuladorClinico.Domain.Entities;

namespace SimuladorClinico.Infrastructure.Persistence;

public class SimuladorClinicoDbContext : DbContext, IUnitOfWork
{
    public SimuladorClinicoDbContext(DbContextOptions<SimuladorClinicoDbContext> options)
        : base(options)
    {
    }

    public DbSet<CasoClinico> CasosClinicos => Set<CasoClinico>();
    public DbSet<SessaoDeSimulacao> SessoesDeSimulacao => Set<SessaoDeSimulacao>();
    public DbSet<InteracaoChat> InteracoesChat => Set<InteracaoChat>();
    public DbSet<Avaliacao> Avaliacoes => Set<Avaliacao>();

    protected override void OnModelCreating(ModelBuilder modelBuilder)
    {
        base.OnModelCreating(modelBuilder);

        modelBuilder.Entity<CasoClinico>(entity =>
        {
            entity.HasKey(e => e.Id);
            entity.Property(e => e.ConhecimentoDescritivo).IsRequired();
            entity.Property(e => e.Sintomas).IsRequired();
            entity.Property(e => e.Restricoes).IsRequired();
            entity.Property(e => e.ValidacaoClinica).IsRequired();
        });

        modelBuilder.Entity<SessaoDeSimulacao>(entity =>
        {
            entity.HasKey(e => e.Id);
            entity.Property(e => e.DataInicio).IsRequired();
            entity.Property(e => e.Estado).IsRequired();

            entity.HasOne(e => e.Caso)
                .WithMany(c => c.SessoesDeSimulacao)
                .HasForeignKey(e => e.CasoId)
                .OnDelete(DeleteBehavior.Restrict);
        });

        modelBuilder.Entity<InteracaoChat>(entity =>
        {
            entity.HasKey(e => e.Id);
            entity.Property(e => e.TextoDaMensagem).IsRequired();
            entity.Property(e => e.Timestamp).IsRequired();
            entity.Property(e => e.Remetente).IsRequired();

            entity.HasOne(e => e.Sessao)
                .WithMany(s => s.InteracoesChat)
                .HasForeignKey(e => e.SessaoId)
                .OnDelete(DeleteBehavior.Cascade);
        });

        modelBuilder.Entity<Avaliacao>(entity =>
        {
            entity.HasKey(e => e.Id);

            entity.HasOne(e => e.Sessao)
                .WithOne(s => s.Avaliacao)
                .HasForeignKey<Avaliacao>(e => e.SessaoId)
                .OnDelete(DeleteBehavior.Cascade);
        });
    }
}
