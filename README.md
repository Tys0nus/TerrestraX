# TerrestraX

Webots-based spider robot project with robot definitions, simulation worlds, controllers, and kinematics tooling.

## What is in this repository

- `controllers/`: Runtime controllers and controller connectors.
- `core/`: Core kinematics, pose, and trajectory modules.
- `robots/`: Robot configuration and modeling support.
- `protos/`: Webots robot/proto definitions.
- `worlds/`: Simulation worlds.
- `architecture.md`: Auto-generated architecture reference.

## Prerequisites

- Python 3.10+
- Webots (R2023+ recommended)

## Quick start

1. Clone the repository.
2. Open Webots and load a world from `worlds/`.
3. Ensure the world controller references one of the controllers under `controllers/`.
4. Run the simulation.

## Development notes

- Keep generated files out of Git (`__pycache__`, notebook checkpoints, local env folders).
- Notebooks are versioned with outputs stripped for cleaner diffs.
- Use `architecture.md` for module boundaries and dependency flow.

## Contributing

See `CONTRIBUTING.md` for development setup, code style, and pull request expectations.

## Security

See `SECURITY.md` for vulnerability reporting.

## License

MIT License. See `LICENSE`.
