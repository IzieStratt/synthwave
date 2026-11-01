class Synthwave < Formula
  include Language::Python::Virtualenv

  desc "Tiny, vibey terminal radio for Lofi Girl's live streams"
  homepage "https://github.com/JosTheDude/synthwave"
  url "https://github.com/JosTheDude/synthwave.git", revision: "0268a0440be09182fad134d4763f8399f8a7ac3c"
  version "0.1.0-0268a04"
  license "MIT"
  head "https://github.com/JosTheDude/synthwave.git", branch: "main"

  depends_on "python@3.13"
  depends_on "mpv"
  depends_on "yt-dlp"

  def install
    venv = virtualenv_create(libexec, "python3.13")
    venv.pip_install_and_link buildpath
  end

  test do
    system libexec/"bin/python", "-c", "import synthwave.app, synthwave.stations"
  end
end
