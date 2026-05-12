FROM mcr.microsoft.com/dotnet/sdk:8.0 AS build
WORKDIR /src

# Copy solution and project files first (layer cache for restore)
COPY SimuladorClinico.sln .
COPY src/SimuladorClinico.Api/*.csproj src/SimuladorClinico.Api/
COPY src/SimuladorClinico.Application/*.csproj src/SimuladorClinico.Application/
COPY src/SimuladorClinico.Domain/*.csproj src/SimuladorClinico.Domain/
COPY src/SimuladorClinico.Infrastructure/*.csproj src/SimuladorClinico.Infrastructure/
RUN dotnet restore

COPY src/ src/
RUN dotnet publish src/SimuladorClinico.Api -c Release -o /out

FROM mcr.microsoft.com/dotnet/aspnet:8.0
WORKDIR /app
COPY --from=build /out .

EXPOSE 5070

ENTRYPOINT ["dotnet", "SimuladorClinico.Api.dll"]
