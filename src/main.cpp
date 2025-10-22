#include <argparse/argparse.hpp>
#include <iostream>

int main(int argc, char *argv[]) {
  argparse::ArgumentParser program("cli");
  program.add_argument("-v").default_value("11").help("a number");

  try {
    program.parse_args(argc, argv);
  } catch (const std::exception &err) {
    std::cerr << err.what() << std::endl;
    std::exit(1);
  }

  std::cout << program.get<std::string>("-v") << std::endl;

  return 0;
};
