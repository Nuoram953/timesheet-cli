use std::env;

use clap::{Parser, Subcommand};
use dotenv::dotenv;
// use log::error;

pub mod commands;
pub mod config;
pub mod jira;

#[derive(Subcommand)]
enum Commands {
    Init {},
}

#[derive(Parser)]
#[command(version, about, long_about = None)]
struct Cli {
    #[arg(short, long, action = clap::ArgAction::Count)]
    debug: u8,

    #[command(subcommand)]
    command: Commands,
}

fn main() -> anyhow::Result<()> {
    dotenv().ok();

    env_logger::init();

    let cli = Cli::parse();

    match &cli.command {
        Commands::Init {} => commands::init::handle(),
    }?;

    Ok(())
}
