# Extensibility by Design

RoboSat.pink extensibility allows to easily custom or enhance only the needed components, and keep everything else as-is.
 

Tools:
------

- To deactivate a tool, just remove the execution right on the related tool file: `chmod -x tools/tool_to_deactivate.py`

- To add a new tool, create a new file, in `robosat_pink/tools` directory, with execution rights and at least thoses two functions:
  - `add_parser(subparser)`
  - `main(args)`

 

Models:
------
- Semantic Segmentation model name can be choose, among availables ones, in the config file.

- To create a new one:
  - In `robosat_pink/models` dir, create a new file: `your_model_name.py`.
  - The file must contains at least one `Model_name` class.
  - These class must itself contains at least `__init__` and `forward` methods.


Losses:
-------

- Loss name can be choose, among availables ones, in the config file.

- To create a new one:
  - In `robosat_pink/losses` dir, create a new file: `your_loss_name.py`.
  - The file must contains at least one `Loss_name` class.
  - These class must itself contains at least `__init__` and `forward` methods.
  - NOTA: If your loss computation is not auto-differentiable by PyTorch, a related `backward` method, will be needed too.


Web UI Templates:
-----------------

- Several RoboSat.pink tools could generate, on demand, a Web UI, with `--web_ui` parameter.
- To switch to your own template, just use `--web_ui_template` extra parameter.
