function summarizeCurrentUser() {
  const user = figma.currentUser;
  if (!user) return null;
  return {
    id: user.id,
    name: user.name,
  };
}

function hasImageFill(node) {
  return "fills" in node && Array.isArray(node.fills) && node.fills.some((fill) => fill.type === "IMAGE");
}

function summarizeNode(node) {
  if (node.type === "TEXT") {
    return {
      id: node.id,
      layerId: node.id,
      name: node.name,
      type: "text",
      supported: true,
      text: node.characters,
      characters: node.characters.length,
    };
  }

  if ("width" in node && "height" in node) {
    return {
      id: node.id,
      layerId: node.id,
      name: node.name,
      type: "imageFill",
      supported: true,
      hasImageFill: hasImageFill(node),
      dimensions: { width: Math.round(node.width), height: Math.round(node.height) },
    };
  }

  return {
    id: node.id,
    layerId: node.id,
    name: node.name,
    type: node.type.toLowerCase(),
    supported: false,
  };
}

function decodeBase64Png(base64) {
  const binary = atob(base64);
  const bytes = new Uint8Array(binary.length);
  for (let index = 0; index < binary.length; index += 1) {
    bytes[index] = binary.charCodeAt(index);
  }
  return bytes;
}

async function createDemoFixture() {
  await figma.loadFontAsync({ family: "Inter", style: "Regular" });

  const frame = figma.createFrame();
  frame.name = "Nova spring campaign demo";
  frame.resize(1280, 1040);
  frame.fills = [{ type: "SOLID", color: { r: 0.96, g: 0.96, b: 0.94 } }];
  frame.x = figma.viewport.center.x - 640;
  frame.y = figma.viewport.center.y - 520;

  const headline = figma.createText();
  headline.name = "Hero headline";
  headline.fontName = { family: "Inter", style: "Regular" };
  headline.characters = "Spring performance gear for every morning run";
  headline.fontSize = 48;
  headline.resize(760, 140);
  headline.x = 80;
  headline.y = 80;

  const cta = figma.createText();
  cta.name = "CTA label";
  cta.fontName = { family: "Inter", style: "Regular" };
  cta.characters = "Shop the new drop";
  cta.fontSize = 28;
  cta.resize(520, 64);
  cta.x = 80;
  cta.y = 250;

  const image = figma.createRectangle();
  image.name = "Image placeholder 1024x1024";
  image.resize(1024, 1024);
  image.x = 880;
  image.y = 8;
  image.fills = [{ type: "SOLID", color: { r: 0.86, g: 0.9, b: 0.98 } }];

  frame.appendChild(headline);
  frame.appendChild(cta);
  frame.appendChild(image);
  figma.currentPage.selection = [headline, cta, image];
  figma.viewport.scrollAndZoomIntoView([frame]);
  figma.notify("Created demo fixture and selected 2 text layers plus a 1024 x 1024 image layer.");
}

async function applyCopy(message) {
  const node = await figma.getNodeByIdAsync(message.layerId);
  if (!node || node.type !== "TEXT") {
    figma.notify("Select a text layer before applying generated copy.", { error: true });
    return;
  }
  if (node.fontName === figma.mixed) {
    figma.notify("Mixed fonts are not supported in the local demo plugin.", { error: true });
    return;
  }
  await figma.loadFontAsync(node.fontName);
  node.characters = message.text;
  figma.notify("Applied generated copy to the selected text layer.");
}

async function applyImage(message) {
  const node = await figma.getNodeByIdAsync(message.layerId);
  if (!node || !("fills" in node)) {
    figma.notify("Select an image-fill-capable layer before applying the placeholder.", { error: true });
    return;
  }
  const image = figma.createImage(decodeBase64Png(message.imageBytesBase64));
  node.fills = [{ type: "IMAGE", scaleMode: "FILL", imageHash: image.hash }];
  figma.notify("Applied simulated 1024 x 1024 placeholder image fill.");
}

function postSelection() {
  figma.ui.postMessage({
    type: "selection",
    fileKey: figma.fileKey,
    pageId: figma.currentPage.id,
    currentUser: summarizeCurrentUser(),
    layers: figma.currentPage.selection.map(summarizeNode),
  });
}

figma.showUI(__html__, { width: 420, height: 620, themeColors: true });
postSelection();

figma.on("selectionchange", postSelection);

figma.ui.onmessage = async (message) => {
  if (message.type === "create-fixture") {
    await createDemoFixture();
    postSelection();
  }

  if (message.type === "apply-copy") {
    await applyCopy(message);
    postSelection();
  }

  if (message.type === "apply-image") {
    await applyImage(message);
    postSelection();
  }

  if (message.type === "close") {
    figma.closePlugin();
  }
};
