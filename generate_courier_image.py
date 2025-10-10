"""
Generate Kuryecini courier team image using Gemini
"""
import asyncio
from emergentintegrations.llm.gemeni.image_generation import GeminiImageGeneration

async def generate_courier_image():
    """Generate professional courier team image"""
    
    # Initialize with Emergent LLM key
    api_key = "sk-emergent-c174948Bc5419E1746"
    image_gen = GeminiImageGeneration(api_key=api_key)
    
    # Detailed prompt for Kuryecini courier team
    prompt = """A dynamic, wide-angle shot of three couriers in Kuryecini's blue and orange uniform. They are posed together on a clean city street at rush hour (motion blur in the background to suggest speed).

The first courier is on a regular bicycle, smiling confidently.
The second courier is on a scooter or electric bicycle, looking energetic.
The third courier is standing next to a small, clean personal car (not a truck), holding a Kuryecini delivery bag.

The atmosphere should be professional, fast-paced, and modern. Use the brand colors bright blue and vibrant orange prominently on the uniforms and logos. 

The style should be high-quality, professional photography, cinematic lighting, and sharp focus on the couriers. Modern Turkish city background, clean and professional aesthetic."""
    
    print("🎨 Generating courier team image with Gemini...")
    print(f"📝 Prompt: {prompt[:100]}...")
    
    try:
        # Generate images
        images = await image_gen.generate_images(
            prompt=prompt,
            model="imagen-3.0-generate-002",
            number_of_images=4  # Generate 4 options
        )
        
        print(f"✅ Generated {len(images)} images")
        
        # Save images
        for i, image_bytes in enumerate(images):
            filename = f"/app/frontend/public/courier_team_{i+1}.png"
            with open(filename, "wb") as f:
                f.write(image_bytes)
            print(f"✅ Saved: {filename}")
        
        print("\n🎉 Image generation complete!")
        print("📁 Images saved to /app/frontend/public/")
        
        return images
        
    except Exception as e:
        print(f"❌ Error generating images: {str(e)}")
        import traceback
        traceback.print_exc()
        return None

if __name__ == "__main__":
    asyncio.run(generate_courier_image())
