use std::io::Cursor;
use std::ops::Deref;
use std::path::Path;

use clap::Parser;
use skim::prelude::{SkimItemReader, SkimOptionsBuilder};
use skim::Skim;
use ssh_cfg::{SshConfig, SshConfigParser};
use tokio::runtime;

#[derive(Parser, Debug)]
#[clap(version, about, long_about = None)]
struct Args {
    /// Print all hosts
    #[clap(short, long, value_parser)]
    list: bool,

    /// SSH config file [default: ~/.ssh/config]
    #[clap(short, long, value_parser)]
    config: Option<String>,
}

async fn parse_ssh_config(config_path: &str) -> Result<SshConfig, anyhow::Error> {
    let path = Path::new(config_path);
    return SshConfigParser::parse(path)
        .await
        .map_err(anyhow::Error::msg);
}

async fn run(args: Args) -> Result<(), Box<dyn std::error::Error>> {
    let config_path_string = args.config.unwrap_or_else(|| "~/.ssh/config".to_string());
    let config_path = config_path_string.deref();
    let ssh_config = parse_ssh_config(config_path).await?;

    let hosts = ssh_config.keys().filter(|k| !k.contains('*'));
    if hosts.clone().count() == 0 {
        println!(
            "Warning: No non-wildcard hosts were found in `{}`.",
            config_path
        );
        return Ok(());
    }

    // List requested: print all hosts
    if args.list {
        for host in hosts {
            println!("{}", host);
        }
        return Ok(());
    }

    // Otherwise, let the user skim through the hosts interactively
    let item_reader = SkimItemReader::default();
    let hosts: Vec<&str> = hosts.map(|h| h.deref()).collect();
    let items = item_reader.of_bufread(Cursor::new(hosts.join("\n")));

    let options = SkimOptionsBuilder::default().build().unwrap();
    let output = Skim::run_with(&options, Some(items)).unwrap();
    if output.is_abort {
        return Ok(());
    }

    for item in output.selected_items.iter() {
        println!("{}", item.output());
    }

    Ok(())
}

fn main() -> Result<(), Box<dyn std::error::Error>> {
    let args = Args::parse();
    let rt = runtime::Builder::new_current_thread().build()?;
    rt.block_on(run(args))
}
