
# Logic Utilities

## Extending the Parsing Logic

The parsing logic is implemented in the `logic_parse` module.

### Adding special cases for parsing.

For any content that is parsed, special cases can be defined. For example in the function `parse_html_body` 
we can add a special case for...
* A specific uri.
```python
if content.loc == AnyUrl('https://www.example.com/some/path'):
    pass
```
* A specific domain.
```python
if content.is_same_host('https://www.example.com'):
    pass
```
* A specific sub_path or list of sub_paths.
```python
if content.is_some_sub_path_from('/some/path'):
    pass
```
* A list of sub_paths.
```python
if content.is_some_sub_path_from_any(['/some/path', '/another/path']):
    pass
```
* Regular expressions.
```python
if content.matches(r'^https://www.example.com/some/path/.*$'):
    pass
```
```python
if content.matches_any([
    r'^https://www.example.com/some/path/.*$', 
    r'^https://www.example.com/another/path/.*$'
]):
    pass
```

This allows us to define cases and update them individually for different sources. 
Analogously, we can define special cases for other parsing functions.



