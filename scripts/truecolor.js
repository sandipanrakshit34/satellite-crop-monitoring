//VERSION=3

function setup() {
  return {
      input: [{
          bands: ["B02", "B03", "B04"]
      }],
      output: {
          bands: 3
      }
  };
}

function evaluatePixel(sample) {
  return [sample.B04, sample.B03, sample.B02];
}
