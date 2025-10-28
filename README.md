### South African Localization

Cohenix ZA_Local is a comprehensive South African localization module for Cohenix ERPthat provides essential features for businesses operating in South Africa. It covers statutory compliance requirements, tax regulations, payroll localization, and financial reporting specific to the South African context.

### Installation

You can install this app using the [bench](https://github.com/frappe/bench) CLI:

```bash
cd $PATH_TO_YOUR_BENCH
bench get-app $URL_OF_THIS_REPO --branch develop
bench install-app za_local
```

### Contributing

This app uses `pre-commit` for code formatting and linting. Please [install pre-commit](https://pre-commit.com/#installation) and enable it for this repository:

```bash
cd apps/za_local
pre-commit install
```

Pre-commit is configured to use the following tools for checking and formatting your code:

- ruff
- eslint
- prettier
- pyupgrade

### License

mit
