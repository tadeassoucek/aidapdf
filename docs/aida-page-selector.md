# Page Selector

Aida uses a bespoke page selector system based on the "Custom Pages" dialogue box in printing software.

The basic format is simple: `1` will select only the first page. `1,2,3` and `1-3` will select the first three pages. `^1` will select the last page, `^2` the penultimate page etc. `1-^1` and `*` will select all pages.

A range can specify a condition: `*{odd}` will select all odd pages. Since `*{even}` and `*{odd}` are common patterns, they can be written more succintly as `even` and `odd`, respectively. Programmatically speaking, specifying only a condition without an associated range assumes that the condition applies to all pages.

Page numbers and page ranges can of course be combined. `1, 5-81{odd}, ^1` will select the first page, all odd pages in the range 5&ndash;81 and the last page.

## Specification

```
spec := <token> ( "," <token> )*

token := <num> | <range>

num := [ "^" ] ( "0".."9" )+

range := [ "*" | <num> "-" <num> ] [ "{" <condition> "}" ] [ <exclude> ]
      := <condition> [ <exclude> ]     // = "*{" <condition> "}"
      := <exclude>                     // = "*" <exclude>

exclude := "!" <token>

condition := <keyword> [ <op> <condition> ]

keyword := "odd" | "even"

op := "or" | "|" | "and" | "&"
```
