     //VERSION=3
     function setup(){
        return{
          input: ["CLP"],
          output: [
            {
              sampleType: "FLOAT32",
              bands: 1
            }
        ]
        }
      }
      
      function evaluatePixel(sample){
        return [sample.CLP/255];
      }