[![Crates.io](https://img.shields.io/crates/v/shf.svg)](https://crates.io/crates/shf)

Simple SSH host finder.
Fuzzy search built-in.

# Table of contents

- [Installation](#installation)
- [Usage](#usage)
- [How to contribute](#how-to-contribute)

# Installation

## From crates.io

```shell
$ cargo install shf
```

## From source

```shell
$ git clone https://github.com/jsmits/shf.git
$ cd shf

# option 1: build executable in current working directory
$ cargo build --release
# put the resulting `target/release/shf` executable on your PATH

# option 2: build and install the resulting executable to the cargo bin directory
$ cargo install --path .
```

# Usage

```shell
$ shf -h
shf 0.1.2
Simple SSH host finder

USAGE:
    shf [OPTIONS]

OPTIONS:
    -c, --config <CONFIG>    SSH config file [default: ~/.ssh/config]
    -h, --help               Print help information
    -l, --list               Print all hosts
    -V, --version            Print version information
```

## Examples

### Fuzzy search through your `~/.ssh/config` hosts

```shell
$ shf
```

### List all hosts from `~/.ssh/config`

```shell
$ shf -l
```

### Use a non-default SSH config file

```shell
# fuzzy search
$ shf -c /path/to/your/ssh/config/file

# list
$ shf -c /path/to/your/ssh/config/file -l
```

### Use a custom fuzzy finder, like [fzf](https://github.com/junegunn/fzf)

```shell
$ shf -l | fzf
```

### Search for a host and directly SSH into it

```shell
# bash/zsh
$ ssh $(shf)

# fish
$ ssh (shf)
```

# How to contribute

Please [create a new issue](https://github.com/jsmits/shf/issues/new) when you encounter a bug 
or have any suggestions or feature requests. Pull requests are also warmly welcomed.
