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

### With `cargo build`
```shell
$ cargo build --release
```
(put the resulting `target/release/shf` on your `PATH`)

### With `cargo install`
```
$ cargo install --path .
```

# Usage

```shell
$ shf -h
shf 0.1.6
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

### Using a non-default SSH config file

#### Fuzzy search
```shell
$ shf -c /path/to/your/ssh/config/file
```

#### List
```shell
$ shf -c /path/to/your/ssh/config/file -l
```

### Using a custom fuzzy finder, like [fzf](https://github.com/junegunn/fzf)

```shell
$ shf -l | fzf
```

### Search for a host and directly SSH into it

#### Bash / Zsh

```shell
$ ssh $(shf)
```

#### Fish
```shell
$ ssh (shf)
```

# How to contribute

Please [create a new issue](https://github.com/jsmits/shf/issues/new) when you encounter a bug 
or have any suggestions or feature requests. Pull requests are welcome as well.
