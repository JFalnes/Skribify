# Scribe v0.1.2

## New features:
* Added support for custom models (GPT 3.5/GPT4)
* Results now saved to `data.json` file

## Bug fixes
* Better support for flask (see Examples/flask for implementation)
* Fixed an issue where the .env wouldn't be saved/loaded properly on first execution
* Fixed argparse typo in `Examples/cli.py`


# Known Issues
* OpenAI API Key is saved in Scribe/.env, which is not ideal. Will be fixed in future versions.
