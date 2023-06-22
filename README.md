# proflow

Proflow is a tool for automating developer workflows. See [our video tutorial](https://www.loom.com/share/95da9891dc1546e185d4a2cd6cbb797a?sid=10124e42-ea97-4d8d-906b-269a2096a748
) for a full introduction.

## Installation

Proflow currently runs as a Linear listening web server. You can enable this by running the `install` then `run` scripts in the top level folder. Also, change the keys in the `.env` file to their respective values, including your OpenAI and Anthropic keys, as well as GitHub information and Linear key.

Once the server is running, just make a Linear ticket, and Proflow will automatically read the files, create a Slack message and pull request with updated code.
