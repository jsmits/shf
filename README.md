[![Crates.io](https://img.shields.io/crates/v/shf.svg)](https://crates.io/crates/shf)

Simple SSH host finder.
Fuzzy search built-in.

# Table of contents

- [Installation](#installation)
    - [From crates.io](#from-cratesio)
    - [From source](#from-source)
- [Usage](#usage)
    - [Examples](#examples)
- [How to contribute](#how-to-contribute)

# Installation

## From [crates.io](https://crates.io/crates/shf)

```shell
$ cargo install shf
```

## From source

```shell
$ git clone https://github.com/jsmits/shf.git
$ cd shf
```

#### `cargo build`

```shell
$ cargo build --release
```

(put the resulting `target/release/shf` on your `PATH`)

#### `cargo install`

```
$ cargo install --path .
```

# Usage

```shell
$ shf -h
shf 0.2.1
Simple SSH host finder

USAGE: shf [OPTIONS]

OPTIONS:
    -l, --list               Print all hosts
    -c, --config <CONFIG>    SSH config file [default: ~/.ssh/config]
    -h, --help               Print help
    -V, --version            Print version
```

## Examples

### Fuzzy search through your hosts

#### in `~/.ssh/config`

```shell
$ shf
```

#### in a different SSH config file

```shell
$ shf -c /path/to/ssh/config
```

### Search a host and directly SSH into it

#### bash / zsh

```shell
$ ssh $(shf)
```

#### fish

```shell
$ ssh (shf)
```

### List all hosts

```shell
$ shf -l
```

# How to contribute

Please [create a new issue](https://github.com/jsmits/shf/issues/new) when you encounter a bug
or have any suggestions or feature requests. Pull requests are welcome as well.
